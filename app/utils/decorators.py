"""Authentication, authorization, ownership, and reauthentication decorators."""

from functools import wraps

from flask import abort, current_app, flash, redirect, request, session, url_for
from flask_login import current_user

from app.utils.redirects import safe_local_path
from app.utils.security import is_reauthentication_fresh


REAUTHENTICATION_RETURN_KEY = "reauthentication_return_to"


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(*roles):
    allowed_roles = frozenset(roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if current_user.role not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def recent_reauthentication_required(view_func):
    """Require a recent password or MFA check before a sensitive operation."""

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        response = _reauthentication_redirect()
        return response if response is not None else view_func(*args, **kwargs)

    return wrapped_view


def recent_reauthentication_required_for_writes(view_func):
    """Require reconfirmation for unsafe HTTP methods without blocking read pages."""

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return view_func(*args, **kwargs)
        response = _reauthentication_redirect()
        return response if response is not None else view_func(*args, **kwargs)

    return wrapped_view


def require_owned_record(record):
    """Hide absent or non-owned records behind the same 404 response."""

    if record is None:
        abort(404)
    return record


def pop_reauthentication_return():
    return session.pop(REAUTHENTICATION_RETURN_KEY, None)


def _reauthentication_redirect():
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()
    if is_reauthentication_fresh(current_user):
        return None

    fallback = url_for("dashboard.dashboard")
    session[REAUTHENTICATION_RETURN_KEY] = safe_local_path(
        request.referrer, fallback=fallback
    )
    flash("Confirm your password or MFA code before continuing.", "warning")
    return redirect(url_for("auth.reconfirm"))
