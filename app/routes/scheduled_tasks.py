from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.repositories import scheduled_task_repository
from app.services import scheduled_task_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from utils.audit import get_audit_context
from utils.helpers import clean_text

tasks_bp = Blueprint("tasks", __name__, url_prefix="/scheduled-tasks")

TASK_TYPES = scheduled_task_service.TASK_TYPES


@tasks_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        task = read_task_form()
        try:
            scheduled_task_service.create_task(
                current_user.id,
                current_user.is_admin,
                task,
                get_audit_context(),
            )
        except ValidationError as exc:
            flash(str(exc), "danger")
            return render_template("tasks/index.html", tasks=get_visible_tasks(), task=task, task_types=TASK_TYPES)
        flash("Scheduled task created.", "success")
        return redirect(url_for("tasks.index"))

    return render_template("tasks/index.html", tasks=get_visible_tasks(), task=None, task_types=TASK_TYPES)


@tasks_bp.route("/<int:task_id>/complete", methods=["POST"])
@login_required
def complete(task_id):
    change_task_status(task_id, "completed")
    flash("Task marked complete.", "success")
    return redirect(url_for("tasks.index"))


@tasks_bp.route("/<int:task_id>/cancel", methods=["POST"])
@login_required
def cancel(task_id):
    change_task_status(task_id, "cancelled")
    flash("Task cancelled.", "info")
    return redirect(url_for("tasks.index"))


def get_visible_tasks(limit=None, status=None):
    return scheduled_task_repository.list_visible(
        current_user.id,
        current_user.is_admin,
        status=status,
        limit=limit,
    )


def get_manageable_task_or_404(task_id):
    access = scheduled_task_repository.find_manageable(
        task_id,
        current_user.id,
        current_user.is_admin,
    )
    if not access.task:
        abort(404)
    if not access.can_manage:
        abort(403)
    return access.task


def read_task_form():
    scope = clean_text(request.form.get("scope")) or "personal"
    if not current_user.is_admin or scope not in {"admin", "global"}:
        scope = "personal"

    due_at = parse_due_at(request.form.get("due_at"))
    return {
        "title": clean_text(request.form.get("title")),
        "description": clean_text(request.form.get("description")),
        "task_type": clean_text(request.form.get("task_type")) or "general",
        "due_at": due_at,
        "scope": scope,
        "user_id": None if scope in {"admin", "global"} else current_user.id,
    }


def change_task_status(task_id, status):
    try:
        return scheduled_task_service.set_status(
            task_id,
            current_user.id,
            current_user.is_admin,
            status,
            get_audit_context(),
        )
    except NotFoundError:
        abort(404)
    except PermissionDeniedError:
        abort(403)


def parse_due_at(raw_value):
    raw_value = clean_text(raw_value)
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None
