from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.admin import ResetPasswordForm, RoleForm
from app.models import db
from app.models.audit_log import AuditLog
from app.models.user import User
from utils.audit import log_audit
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users_list)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def update_role(user_id):
    user = User.query.get_or_404(user_id)
    form = RoleForm()
    if form.validate_on_submit():
        user.role = form.role.data
        log_audit("role_updated", f"{user.email} role changed to {user.role}")
        db.session.commit()
        flash("User role updated.", "success")
    else:
        flash("Choose a valid role.", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@login_required
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot ban your own account.", "danger")
        return redirect(url_for("admin.users"))

    user.is_banned = True
    log_audit("user_banned", f"{user.email} was banned")
    db.session.commit()
    flash("User banned.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@login_required
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    log_audit("user_unbanned", f"{user.email} was unbanned")
    db.session.commit()
    flash("User unbanned.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit() and form.password.data:
        user.set_password(form.password.data)
        log_audit("password_reset", f"Password reset for {user.email}")
        db.session.commit()
        flash("Password reset successfully.", "success")
    else:
        flash("Password must be at least 8 characters.", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    page = request.args.get("page", 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page,
        per_page=25,
        error_out=False,
    )
    return render_template("admin/audit_logs.html", logs=logs)
