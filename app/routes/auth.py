from datetime import datetime
from io import BytesIO

import pyotp
import qrcode
from flask import Blueprint, abort, flash, redirect, render_template, send_file, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms.auth import ChangePasswordForm, LoginForm, MfaSetupForm, MfaTokenForm, RegisterForm
from app.models.user import User
from utils.audit import log_audit
from utils.db import execute, fetch_one

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

try:
    from app.models import limiter
except ImportError:
    limiter = None

login_rate_limit = limiter.limit("5 per minute") if limiter else (lambda view: view)
password_rate_limit = limiter.limit("5 per 15 minutes") if limiter else (lambda view: view)

LOCKOUT_FAILURE_LIMIT = 5
LOCKOUT_MINUTES = 15


@auth_bp.route("/register", methods=["GET", "POST"])
@login_rate_limit
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        existing_user = User.from_row(fetch_one("SELECT * FROM users WHERE email = %s", (email,)))
        if existing_user:
            flash("Email already exists.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(display_name=form.display_name.data.strip(), email=email)
        user.set_password(form.password.data)

        execute(
            """
            INSERT INTO users (email, password_hash, display_name, role, is_banned, mfa_secret, mfa_enabled, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (
                user.email,
                user.password_hash,
                user.display_name,
                user.role,
                int(user.is_banned),
                user.mfa_secret,
                int(user.mfa_enabled),
            ),
        )
        log_audit("register", f"New account registered for {email}", user=user)

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@login_rate_limit
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        user = User.from_row(fetch_one("SELECT * FROM users WHERE email = %s", (email,)))

        if user and is_account_locked(user):
            log_audit("login_locked", f"Login blocked for {email}; locked until {user.locked_until}", user=user)
            flash("Too many failed login attempts. Try again later.", "danger")
            return render_template("auth/login.html", form=form)

        if not user:
            log_audit("login_failed", f"Failed login for unknown account {email}")
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.check_password(form.password.data):
            record_failed_login(user, email)
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if user.is_banned:
            log_audit("login_blocked", f"Banned user tried to log in: {email}", user=user)
            flash("This account is banned. Contact an administrator.", "danger")
            return render_template("auth/login.html", form=form)

        reset_failed_logins(user)

        if user.mfa_enabled:
            session["pending_mfa_user_id"] = user.id
            session.permanent = True
            return redirect(url_for("auth.verify_mfa"))

        login_user(user)
        session.permanent = True
        session["auth_version"] = user.auth_version
        log_audit("login", "User logged in", user=user)
        flash("Logged in successfully.", "success")
        return redirect_after_login(user)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/mfa/verify", methods=["GET", "POST"])
@login_rate_limit
def verify_mfa():
    user_id = session.get("pending_mfa_user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("auth.login"))
    form = MfaTokenForm()
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(form.token.data.strip(), valid_window=1):
            log_audit("mfa_failed", "Invalid MFA token", user=user)
            flash("Invalid MFA code.", "danger")
            return render_template("auth/verify_mfa.html", form=form)

        session.pop("pending_mfa_user_id", None)
        session.permanent = True
        login_user(user)
        session["auth_version"] = user.auth_version
        log_audit("login", "User logged in with MFA", user=user)
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

    if not current_user.mfa_secret:
        current_user.mfa_secret = pyotp.random_base32()
        execute("UPDATE users SET mfa_secret = %s, updated_at = NOW() WHERE id = %s", (current_user.mfa_secret, current_user.id))

    totp = pyotp.TOTP(current_user.mfa_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Cyber Dashboard",
    )

    if form.validate_on_submit():
        if not totp.verify(form.token.data.strip(), valid_window=1):
            flash("Invalid MFA code.", "danger")
            return render_template(
                "auth/setup_mfa.html",
                form=form,
                password_form=password_form,
                provisioning_uri=provisioning_uri,
            )

        current_user.mfa_enabled = True
        execute("UPDATE users SET mfa_enabled = 1, updated_at = NOW() WHERE id = %s", (current_user.id,))
        log_audit("mfa_enabled", "User enabled MFA")
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

    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (current_user.id,)))
    if not user or not user.check_password(form.current_password.data):
        log_audit("password_change_failed", "Current password verification failed")
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("auth.setup_mfa"))

    if user.check_password(form.new_password.data):
        flash("Your new password must be different from your current password.", "danger")
        return redirect(url_for("auth.setup_mfa"))

    user.set_password(form.new_password.data)
    execute(
        """
        UPDATE users
        SET password_hash = %s, auth_version = auth_version + 1, updated_at = NOW()
        WHERE id = %s
        """,
        (user.password_hash, current_user.id),
    )
    log_audit("password_changed", "User changed their own password")
    logout_user()
    session.clear()
    flash("Password changed. Please log in again on this device.", "success")
    return redirect(url_for("auth.login"))


def redirect_after_login(user):
    if getattr(user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))
    return redirect(url_for("dashboard.user_dashboard"))


def is_account_locked(user):
    if not user.locked_until:
        return False

    locked_until = user.locked_until
    if isinstance(locked_until, str):
        try:
            locked_until = datetime.fromisoformat(locked_until)
        except ValueError:
            return False

    return locked_until > datetime.now()


def record_failed_login(user, email):
    next_failure_count = user.failed_login_count + 1
    execute(
        """
        UPDATE users
        SET failed_login_count = failed_login_count + 1,
            last_failed_login_at = NOW(),
            locked_until = CASE
                WHEN failed_login_count + 1 >= %s THEN TIMESTAMPADD(MINUTE, %s, NOW())
                ELSE locked_until
            END,
            updated_at = NOW()
        WHERE id = %s
        """,
        (LOCKOUT_FAILURE_LIMIT, LOCKOUT_MINUTES, user.id),
    )

    if next_failure_count >= LOCKOUT_FAILURE_LIMIT:
        log_audit(
            "login_failed",
            f"Failed login for {email}; account locked for {LOCKOUT_MINUTES} minutes after {next_failure_count} attempts",
            user=user,
        )
        return

    log_audit("login_failed", f"Failed login for {email}; failed attempts: {next_failure_count}", user=user)


def reset_failed_logins(user):
    execute(
        """
        UPDATE users
        SET failed_login_count = 0,
            last_failed_login_at = NULL,
            locked_until = NULL,
            updated_at = NOW()
        WHERE id = %s
        """,
        (user.id,),
    )
