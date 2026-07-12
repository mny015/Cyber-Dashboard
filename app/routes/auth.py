from io import BytesIO

import pyotp
import qrcode
from flask import Blueprint, abort, flash, redirect, render_template, send_file, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import limiter
from app.forms.auth import ChangePasswordForm, LoginForm, MfaSetupForm, MfaTokenForm, RegisterForm
from app.repositories import user_repository
from app.services import auth_service
from app.services.exceptions import ConflictError, ValidationError
from utils.audit import get_audit_context, log_audit

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

login_rate_limit = limiter.limit("5 per minute")
password_rate_limit = limiter.limit("5 per 15 minutes")

@auth_bp.route("/register", methods=["GET", "POST"])
@login_rate_limit
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        try:
            auth_service.register(
                form.display_name.data,
                email,
                form.password.data,
                get_audit_context(),
            )
        except ConflictError as exc:
            flash(str(exc), "danger")
            return render_template("auth/register.html", form=form)

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@login_rate_limit
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        decision = auth_service.authenticate(
            email, form.password.data, get_audit_context()
        )
        user = decision.user
        if decision.status == "locked":
            flash("Too many failed login attempts. Try again later.", "danger")
            return render_template("auth/login.html", form=form)
        if decision.status == "invalid":
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)
        if decision.status == "banned":
            flash("This account is banned. Contact an administrator.", "danger")
            return render_template("auth/login.html", form=form)
        if decision.status == "mfa_required":
            session["pending_mfa_user_id"] = user.id
            session.permanent = True
            return redirect(url_for("auth.verify_mfa"))

        login_user(user)
        session.permanent = True
        session["auth_version"] = user.auth_version
        auth_service.record_login(user, get_audit_context(user))
        flash("Logged in successfully.", "success")
        return redirect_after_login(user)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/mfa/verify", methods=["GET", "POST"])
@login_rate_limit
def verify_mfa():
    user_id = session.get("pending_mfa_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = user_repository.find_by_id(user_id)
    if not user:
        return redirect(url_for("auth.login"))
    form = MfaTokenForm()
    if form.validate_on_submit():
        if not auth_service.verify_mfa_token(
            user, form.token.data, get_audit_context(user), audit_failure=True
        ):
            flash("Invalid MFA code.", "danger")
            return render_template("auth/verify_mfa.html", form=form)

        session.pop("pending_mfa_user_id", None)
        session.permanent = True
        login_user(user)
        session["auth_version"] = user.auth_version
        auth_service.record_login(user, get_audit_context(user), used_mfa=True)
        flash("Logged in successfully.", "success")
        return redirect_after_login(user)

    return render_template("auth/verify_mfa.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    log_audit("logout", "User logged out")
    logout_user()
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile/mfa", methods=["GET", "POST"])
@login_required
def setup_mfa():
    form = MfaSetupForm()
    password_form = ChangePasswordForm()
    if current_user.mfa_enabled:
        return render_template(
            "auth/setup_mfa.html",
            form=form,
            password_form=password_form,
            provisioning_uri=None,
        )

    auth_service.ensure_mfa_secret(current_user)

    totp = pyotp.TOTP(current_user.mfa_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Cyber Dashboard",
    )

    if form.validate_on_submit():
        try:
            auth_service.enable_mfa(
                current_user, form.token.data, get_audit_context()
            )
        except ValidationError as exc:
            flash(str(exc), "danger")
            return render_template(
                "auth/setup_mfa.html",
                form=form,
                password_form=password_form,
                provisioning_uri=provisioning_uri,
            )
        flash("MFA enabled successfully.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template(
        "auth/setup_mfa.html",
        form=form,
        password_form=password_form,
        provisioning_uri=provisioning_uri,
    )


@auth_bp.route("/profile/mfa/qr")
@login_required
def mfa_qr():
    if current_user.mfa_enabled:
        abort(404)
    if not current_user.mfa_secret:
        flash("Start MFA setup first.", "warning")
        return redirect(url_for("auth.setup_mfa"))

    uri = pyotp.TOTP(current_user.mfa_secret).provisioning_uri(
        name=current_user.email,
        issuer_name="Cyber Dashboard",
    )
    image = qrcode.make(uri)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")


@auth_bp.route("/profile/password", methods=["POST"])
@login_required
@password_rate_limit
def change_password():
    form = ChangePasswordForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("auth.setup_mfa"))

    try:
        auth_service.change_password(
            current_user.id,
            form.current_password.data,
            form.new_password.data,
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("auth.setup_mfa"))
    logout_user()
    session.clear()
    flash("Password changed. Please log in again on this device.", "success")
    return redirect(url_for("auth.login"))


def redirect_after_login(user):
    if getattr(user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))
    return redirect(url_for("dashboard.user_dashboard"))
