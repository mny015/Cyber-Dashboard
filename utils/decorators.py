from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user


def admin_required(view_func):
	@wraps(view_func)
	def wrapped_view(*args, **kwargs):
		if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
			flash("Admin access required.", "danger")
			abort(403)
		return view_func(*args, **kwargs)

	return wrapped_view


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in first.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
