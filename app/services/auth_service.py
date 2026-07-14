"""Registration, account lockout, password, and MFA business workflows."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import pyotp

from app.models import User
from app.repositories import user_repository
from app.services import audit_service
from app.services.exceptions import ConflictError, ValidationError
from app.utils.database import db, transaction
from app.utils.datetime_helpers import parse_datetime
from app.utils.security import verify_reauthentication


LOCKOUT_FAILURE_LIMIT = 5
LOCKOUT_MINUTES = 15


@dataclass(frozen=True, slots=True)
class LoginDecision:
    status: str
    user: User | None = None


def register(display_name, email, password, context):
    normalized_email = email.lower().strip()
    if user_repository.find_by_email(normalized_email):
        raise ConflictError("Email already exists.")

    user = User(display_name=display_name.strip(), email=normalized_email)
    user.set_password(password)
    with transaction() as cursor:
        database = db.using(cursor)
        user_repository.create(user, database=database)
        audit_service.record(
            "register",
            f"New account registered for {normalized_email}",
            context=_as_actor(context, user.id),
            database=database,
        )
    return user


def authenticate(email, password, context):
    normalized_email = email.lower().strip()
    user = user_repository.find_by_email(normalized_email)
    if user and is_account_locked(user):
        audit_service.record(
            "login_locked",
            f"Login blocked for {normalized_email}; locked until {user.locked_until}",
            _as_actor(context, user.id),
        )
        return LoginDecision("locked", user)
    if not user:
        audit_service.record(
            "login_failed", f"Failed login for unknown account {normalized_email}", context
        )
        return LoginDecision("invalid")
    if not user.check_password(password):
        record_failed_login(user, normalized_email, context)
        return LoginDecision("invalid", user)
    if user.is_banned:
        audit_service.record(
            "login_blocked",
            f"Banned user tried to log in: {normalized_email}",
            _as_actor(context, user.id),
        )
        return LoginDecision("banned", user)

    user_repository.reset_failed_logins(user.id)
    return LoginDecision("mfa_required" if user.mfa_enabled else "authenticated", user)


def record_login(user, context, used_mfa=False):
    details = "User logged in with MFA" if used_mfa else "User logged in"
    audit_service.record("login", details, _as_actor(context, user.id))


def record_failed_login(user, email, context):
    next_count = _next_failure_count(user)
    with transaction() as cursor:
        user_repository.record_failed_login(
            user.id, LOCKOUT_FAILURE_LIMIT, LOCKOUT_MINUTES, cursor=cursor
        )
        details = f"Failed login for {email}; failed attempts: {next_count}"
        if next_count >= LOCKOUT_FAILURE_LIMIT:
            details = (
                f"Failed login for {email}; account locked for {LOCKOUT_MINUTES} "
                f"minutes after {next_count} attempts"
            )
        audit_service.record(
            "login_failed",
            details,
            _as_actor(context, user.id),
            database=db.using(cursor),
        )


def is_account_locked(user, now=None):
    if not user.locked_until:
        return False
    locked_until = user.locked_until
    if isinstance(locked_until, str):
        try:
            locked_until = parse_datetime(locked_until)
        except ValueError:
            return False
    return locked_until > (now or datetime.now())


def ensure_mfa_secret(user):
    if user.mfa_secret:
        return user.mfa_secret
    user.mfa_secret = pyotp.random_base32()
    user_repository.set_mfa_secret(user.id, user.mfa_secret)
    return user.mfa_secret


def verify_mfa_token(user, token, context=None, audit_failure=False):
    valid = bool(user.mfa_secret) and pyotp.TOTP(user.mfa_secret).verify(
        token.strip(), valid_window=1
    )
    if not valid and audit_failure:
        audit_service.record("mfa_failed", "Invalid MFA token", _as_actor(context, user.id))
    return valid


def enable_mfa(user, token, context):
    if not verify_mfa_token(user, token):
        raise ValidationError("Invalid MFA code.")
    with transaction() as cursor:
        database = db.using(cursor)
        user_repository.set_mfa_enabled(user.id, True, database=database)
        audit_service.record(
            "mfa_enabled", "User enabled MFA", _as_actor(context, user.id), database
        )
    user.mfa_enabled = True


def change_password(user_id, current_password, new_password, context):
    user = user_repository.find_by_id(user_id)
    if not user or not user.check_password(current_password):
        audit_service.record(
            "password_change_failed",
            "Current password verification failed",
            _as_actor(context, user_id),
        )
        raise ValidationError("Current password is incorrect.")
    if user.check_password(new_password):
        raise ValidationError("Your new password must be different from your current password.")

    user.set_password(new_password)
    with transaction() as cursor:
        database = db.using(cursor)
        user_repository.update_password(
            user.id, user.password_hash, user.auth_version + 1, database=database
        )
        audit_service.record(
            "password_changed",
            "User changed their own password",
            _as_actor(context, user.id),
            database,
        )


def reconfirm_identity(user, current_password, mfa_token, context):
    if not verify_reauthentication(user, current_password, mfa_token):
        audit_service.record(
            "reauthentication_failed",
            "Sensitive-action identity confirmation failed",
            _as_actor(context, user.id),
        )
        raise ValidationError("Password or MFA code is incorrect.")
    audit_service.record(
        "reauthentication_succeeded",
        "Identity confirmed for a sensitive action",
        _as_actor(context, user.id),
    )


def _as_actor(context, actor_id):
    context = context or audit_service.AuditContext()
    return audit_service.AuditContext(actor_id=actor_id, ip_address=context.ip_address)


def _next_failure_count(user, now=None):
    last_failed = user.last_failed_login_at
    if isinstance(last_failed, str):
        try:
            last_failed = parse_datetime(last_failed)
        except ValueError:
            last_failed = None
    if not last_failed or last_failed < (now or datetime.now()) - timedelta(
        minutes=LOCKOUT_MINUTES
    ):
        return 1
    return user.failed_login_count + 1
