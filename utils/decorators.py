from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def admin_required(view_func):
	@wraps(view_func)
	def wrapped_view(*args, **kwargs):
		if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
			flash("Admin access required.", "danger")
			return redirect(url_for("dashboard.dashboard"))
		return view_func(*args, **kwargs)

	return wrapped_view
