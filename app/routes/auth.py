from io import BytesIO

import pyotp
import qrcode
from flask import Blueprint, flash, redirect, render_template, send_file, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms.auth import LoginForm, MfaSetupForm, MfaTokenForm, RegisterForm
from app.models import db, limiter
from app.models.user import User
from utils.audit import log_audit

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
login_rate_limit = limiter.limit("5 per minute") if limiter else (lambda view: view)


@auth_bp.route("/register", methods=["GET", "POST"])
@login_rate_limit
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        existing_user = User.query.filter(User.email == email).first()
        if existing_user:
            flash("Email already exists.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(display_name=form.display_name.data.strip(), email=email)
        user.set_password(form.password.data)

        db.session.add(user)
        log_audit("register", f"New account registered for {email}", user=user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@login_rate_limit
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(form.password.data):
            log_audit("login_failed", f"Failed login for {email}")
            db.session.commit()
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if user.is_banned:
            log_audit("login_blocked", f"Banned user tried to log in: {email}", user=user)
            db.session.commit()
            flash("This account is banned. Contact an administrator.", "danger")
            return render_template("auth/login.html", form=form)

        if user.mfa_enabled:
            session["pending_mfa_user_id"] = user.id
            session.permanent = True
            return redirect(url_for("auth.verify_mfa"))

        login_user(user)
        session.permanent = True
        log_audit("login", "User logged in", user=user)
        db.session.commit()
        flash("Logged in successfully.", "success")
        return redirect_after_login(user)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/mfa/verify", methods=["GET", "POST"])
@login_rate_limit
def verify_mfa():
    user_id = session.get("pending_mfa_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(user_id)
    form = MfaTokenForm()
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(form.token.data.strip(), valid_window=1):
            log_audit("mfa_failed", "Invalid MFA token", user=user)
            db.session.commit()
            flash("Invalid MFA code.", "danger")
            return render_template("auth/verify_mfa.html", form=form)

        session.pop("pending_mfa_user_id", None)
        session.permanent = True
        login_user(user)
        log_audit("login", "User logged in with MFA", user=user)
        db.session.commit()
        flash("Logged in successfully.", "success")
        return redirect_after_login(user)

    return render_template("auth/verify_mfa.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_audit("logout", "User logged out")
    db.session.commit()
    logout_user()
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile/mfa", methods=["GET", "POST"])
@login_required
def setup_mfa():
    form = MfaSetupForm()
    if not current_user.mfa_secret:
        current_user.mfa_secret = pyotp.random_base32()
        db.session.commit()

    totp = pyotp.TOTP(current_user.mfa_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Cyber Dashboard",
    )

    if form.validate_on_submit():
        if not totp.verify(form.token.data.strip(), valid_window=1):
            flash("Invalid MFA code.", "danger")
            return render_template("auth/setup_mfa.html", form=form, provisioning_uri=provisioning_uri)

        current_user.mfa_enabled = True
        log_audit("mfa_enabled", "User enabled MFA")
        db.session.commit()
        flash("MFA enabled successfully.", "success")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("auth/setup_mfa.html", form=form, provisioning_uri=provisioning_uri)


@auth_bp.route("/profile/mfa/qr")
@login_required
def mfa_qr():
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


def redirect_after_login(user):
    if getattr(user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))
    return redirect(url_for("dashboard.user_dashboard"))
