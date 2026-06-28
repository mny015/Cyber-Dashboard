from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.admin import ResetPasswordForm, RoleForm
from app.models.user import User
from utils.audit import log_audit
from utils.decorators import admin_required
from utils.db import execute, fetch_all, fetch_one

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users_list = [User.from_row(row) for row in fetch_all("SELECT * FROM users ORDER BY created_at DESC")]
    return render_template("admin/users.html", users=users_list)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def update_role(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("admin.users"))
    form = RoleForm()
    if form.validate_on_submit():
        user.role = form.role.data
        execute("UPDATE users SET role = %s, updated_at = NOW() WHERE id = %s", (user.role, user.id))
        log_audit("role_updated", f"{user.email} role changed to {user.role}")
        flash("User role updated.", "success")
    else:
        flash("Choose a valid role.", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@login_required
@admin_required
def ban_user(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("You cannot ban your own account.", "danger")
        return redirect(url_for("admin.users"))

    user.is_banned = True
    execute("UPDATE users SET is_banned = 1, updated_at = NOW() WHERE id = %s", (user.id,))
    log_audit("user_banned", f"{user.email} was banned")
    flash("User banned.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@login_required
@admin_required
def unban_user(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("admin.users"))
    user.is_banned = False
    execute("UPDATE users SET is_banned = 0, updated_at = NOW() WHERE id = %s", (user.id,))
    log_audit("user_unbanned", f"{user.email} was unbanned")
    flash("User unbanned.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("admin.users"))
    form = ResetPasswordForm()
    if form.validate_on_submit() and form.password.data:
        user.set_password(form.password.data)
        execute("UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s", (user.password_hash, user.id))
        log_audit("password_reset", f"Password reset for {user.email}")
        flash("Password reset successfully.", "success")
    else:
        flash("Password must be at least 8 characters.", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * 25
    rows = fetch_all(
        """
        SELECT audit_logs.*, users.email AS user_email
        FROM audit_logs
        LEFT JOIN users ON users.id = audit_logs.user_id
        ORDER BY audit_logs.created_at DESC
        LIMIT 25 OFFSET %s
        """,
        (offset,),
    )
    total_row = fetch_one("SELECT COUNT(*) AS total FROM audit_logs")
    logs = type("Pagination", (), {"items": rows, "page": page, "pages": 1, "total": total_row["total"] if total_row else 0, "has_next": False, "has_prev": page > 1})()
    return render_template("admin/audit_logs.html", logs=logs)
