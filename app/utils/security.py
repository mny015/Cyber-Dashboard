"""Focused security primitives shared by authentication and HTTP utilities."""

import base64
import hashlib
import hmac
import ipaddress
import time

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app, request, session
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash


MFA_SECRET_PREFIX = "mfa:v1:"
REAUTHENTICATED_AT_KEY = "reauthenticated_at"
REAUTHENTICATED_VERSION_KEY = "reauthenticated_auth_version"


class SecretProtectionError(RuntimeError):
    """Raised when protected credential material cannot be decrypted safely."""


def configure_trusted_proxy(app):
    """Trust forwarding headers only when an explicit proxy hop count is configured."""

    trusted_hops = int(app.config.get("TRUSTED_PROXY_HOPS", 0))
    if trusted_hops > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=trusted_hops,
            x_proto=trusted_hops,
        )


def get_client_address():
    """Return the validated peer address after any configured ProxyFix processing."""

    candidate = (request.remote_addr or "").strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return ""


def pseudonymous_rate_key(namespace, value):
    """Build a stable rate-limit key without storing account identifiers in clear text."""

    normalized = str(value or "").strip().lower()
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    digest = hmac.new(secret, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{namespace}:{digest}"


def hash_password(password):
    """Hash a password with Werkzeug's memory-hard scrypt implementation."""

    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash, password):
    return bool(password_hash) and check_password_hash(password_hash, password)


def encrypt_mfa_secret(secret):
    """Encrypt a TOTP secret with application key material kept outside MySQL."""

    if not secret:
        return None
    if is_encrypted_mfa_secret(secret):
        return secret
    encrypted = _mfa_cipher().encrypt(str(secret).encode("utf-8")).decode("ascii")
    return f"{MFA_SECRET_PREFIX}{encrypted}"


def decrypt_mfa_secret(stored_secret):
    """Decrypt an encrypted TOTP secret while accepting legacy plaintext for rotation."""

    if not stored_secret:
        return None
    if not is_encrypted_mfa_secret(stored_secret):
        return str(stored_secret)
    token = str(stored_secret)[len(MFA_SECRET_PREFIX) :]
    try:
        return _mfa_cipher().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise SecretProtectionError("Protected MFA data could not be read.") from exc


def is_encrypted_mfa_secret(value):
    return isinstance(value, str) and value.startswith(MFA_SECRET_PREFIX)


def verify_reauthentication(user, password="", mfa_token=""):
    """Accept the account password or, when enabled, a valid current TOTP token."""

    if password and user.check_password(password):
        return True
    if mfa_token and user.mfa_enabled and user.mfa_secret:
        return pyotp.TOTP(user.mfa_secret).verify(mfa_token.strip(), valid_window=1)
    return False


def mark_reauthenticated(user):
    session[REAUTHENTICATED_AT_KEY] = int(time.time())
    session[REAUTHENTICATED_VERSION_KEY] = int(user.auth_version or 0)


def clear_reauthentication():
    session.pop(REAUTHENTICATED_AT_KEY, None)
    session.pop(REAUTHENTICATED_VERSION_KEY, None)


def is_reauthentication_fresh(user, now=None):
    authenticated_at = session.get(REAUTHENTICATED_AT_KEY)
    authenticated_version = session.get(REAUTHENTICATED_VERSION_KEY)
    if authenticated_at is None or authenticated_version != int(user.auth_version or 0):
        return False
    try:
        age = int(now or time.time()) - int(authenticated_at)
    except (TypeError, ValueError):
        return False
    maximum_age = int(current_app.config.get("REAUTHENTICATION_MAX_AGE", 600))
    return 0 <= age <= maximum_age


def _mfa_cipher():
    configured_key = str(current_app.config.get("MFA_ENCRYPTION_KEY", "")).strip()
    if configured_key:
        key = configured_key.encode("ascii")
    else:
        secret_key = current_app.config["SECRET_KEY"].encode("utf-8")
        key = base64.urlsafe_b64encode(hashlib.sha256(secret_key).digest())
    try:
        return Fernet(key)
    except (TypeError, ValueError) as exc:
        raise SecretProtectionError("MFA encryption is not configured correctly.") from exc
