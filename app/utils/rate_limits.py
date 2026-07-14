"""Reusable rate-limit policies and privacy-preserving account keys."""

from flask import request, session
from flask_login import current_user

from app.extensions import limiter
from app.utils.security import get_client_address, pseudonymous_rate_key


LOGIN_PER_IP = "10 per minute"
LOGIN_PER_ACCOUNT = "8 per 15 minutes"
REGISTRATION_PER_IP = "5 per hour"
REGISTRATION_PER_ACCOUNT = "3 per hour"
MFA_PER_IP = "10 per 10 minutes"
MFA_PER_ACCOUNT = "5 per 5 minutes"
PASSWORD_PER_IP = "10 per hour"
PASSWORD_PER_ACCOUNT = "5 per 15 minutes"
SENSITIVE_PER_IP = "20 per hour"
SENSITIVE_PER_ACCOUNT = "10 per 15 minutes"


def login_rate_limited(view_func):
    limited = limiter.limit(LOGIN_PER_ACCOUNT, key_func=_email_account_key)(view_func)
    return limiter.limit(LOGIN_PER_IP, key_func=get_client_address)(limited)


def registration_rate_limited(view_func):
    limited = limiter.limit(REGISTRATION_PER_ACCOUNT, key_func=_email_account_key)(view_func)
    return limiter.limit(REGISTRATION_PER_IP, key_func=get_client_address)(limited)


def mfa_rate_limited(view_func):
    limited = limiter.limit(MFA_PER_ACCOUNT, key_func=_pending_mfa_key)(view_func)
    return limiter.limit(MFA_PER_IP, key_func=get_client_address)(limited)


def password_rate_limited(view_func):
    limited = limiter.limit(PASSWORD_PER_ACCOUNT, key_func=_authenticated_account_key)(
        view_func
    )
    return limiter.limit(PASSWORD_PER_IP, key_func=get_client_address)(limited)


def sensitive_action_rate_limited(view_func):
    limited = limiter.limit(SENSITIVE_PER_ACCOUNT, key_func=_authenticated_account_key)(
        view_func
    )
    return limiter.limit(SENSITIVE_PER_IP, key_func=get_client_address)(limited)


def _email_account_key():
    email = request.form.get("email", "")
    if not email:
        return f"ip:{get_client_address()}"
    return pseudonymous_rate_key("login-account", email)


def _pending_mfa_key():
    user_id = session.get("pending_mfa_user_id")
    if user_id is None:
        return f"ip:{get_client_address()}"
    return pseudonymous_rate_key("pending-mfa", user_id)


def _authenticated_account_key():
    if not current_user.is_authenticated:
        return f"ip:{get_client_address()}"
    return pseudonymous_rate_key("account", current_user.id)
