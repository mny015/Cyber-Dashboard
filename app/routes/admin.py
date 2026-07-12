from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.forms.admin import AdminPasswordResetForm, RoleForm
from app.repositories import (
    audit_repository,
    category_repository,
    notification_repository,
    topic_repository,
    user_repository,
)
from app.services import notification_service, user_management_service
from app.services.exceptions import (
    ConflictError,
    LastAdministratorError,
    NotFoundError,
    PermissionDeniedError,
)
from utils.audit import get_audit_context
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    return render_template("admin/users.html", users=user_repository.list_all())


@admin_bp.route("/topics")
@login_required
@admin_required
def topic_summaries():
    return render_template(
        "admin/topic_summaries.html",
        topics=topic_repository.list_admin_summaries(),
    )


@admin_bp.route("/topics/<int:topic_id>/request-notes", methods=["POST"])
@login_required
@admin_required
def request_topic_notes(topic_id):
    try:
        notification_service.request_note_access(
            topic_id, current_user.id, get_audit_context()
        )
    except NotFoundError:
        abort(404)
    except PermissionDeniedError as exc:
        flash(str(exc), "info")
        return redirect(url_for("admin.topic_summaries"))
    except ConflictError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("admin.note_requests"))
    flash("Note access request sent to the user.", "success")
    return redirect(url_for("admin.note_requests"))


@admin_bp.route("/note-requests")
@login_required
@admin_required
def note_requests():
    return render_template(
        "admin/note_requests.html",
        requests=notification_repository.list_for_admin(current_user.id),
    )


@admin_bp.route("/note-requests/<int:request_id>/note")
@login_required
@admin_required
def approved_note(request_id):
    note = notification_repository.find_approved_note(request_id, current_user.id)
    if not note:
        abort(404)
    return render_template("admin/approved_note.html", note=note)


@admin_bp.route("/categories")
@login_required
@admin_required
def category_summaries():
    return render_template(
        "admin/category_summaries.html",
        categories=category_repository.list_admin_summaries(),
    )


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def update_role(user_id):
    user = user_repository.find_by_id(user_id)
    if not user:
        return redirect(url_for("admin.users"))
    form = RoleForm()
    if form.validate_on_submit():
        try:
            user_management_service.change_role(
                user.id,
                current_user.id,
                form.role.data,
                get_audit_context(),
            )
        except (PermissionDeniedError, LastAdministratorError) as exc:
            flash(str(exc), "danger")
            return redirect(url_for("admin.users"))
        flash("User role updated.", "success")
    else:
        flash("Choose a valid role.", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@login_required
@admin_required
def ban_user(user_id):
    user = user_repository.find_by_id(user_id)
    if not user:
        return redirect(url_for("admin.users"))
    try:
        user_management_service.set_banned(
            user.id, current_user.id, True, get_audit_context()
        )
    except (PermissionDeniedError, LastAdministratorError) as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.users"))
    flash("User banned.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@login_required
@admin_required
def unban_user(user_id):
    user = user_repository.find_by_id(user_id)
    if not user:
        return redirect(url_for("admin.users"))
    user_management_service.set_banned(
        user.id, current_user.id, False, get_audit_context()
    )
    flash("User unbanned.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/password", methods=["POST"])
@login_required
@admin_required
def reset_user_password(user_id):
    user = user_repository.find_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("Use your own Security page to change your password.", "danger")
        return redirect(url_for("admin.users"))

    form = AdminPasswordResetForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("admin.users"))

    user_management_service.reset_password(
        user.id,
        current_user.id,
        form.password.data,
        get_audit_context(),
    )
    flash(f"Password updated for {user.display_name}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = user_repository.find_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))
    try:
        user_management_service.delete_user(
            user.id,
            current_user.id,
            current_user.email,
            get_audit_context(),
        )
    except (PermissionDeniedError, LastAdministratorError) as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.users"))
    flash(f"{user.display_name} was deleted.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    page = request.args.get("page", 1, type=int)
    return render_template("admin/audit_logs.html", logs=audit_repository.paginate(page))
