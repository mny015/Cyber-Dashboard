"""HTTP handlers for scheduled task management."""

from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.repositories import scheduled_task_repository
from app.services import scheduled_task_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from utils.audit import get_audit_context
from utils.helpers import clean_text


TASK_TYPES = scheduled_task_service.TASK_TYPES


@login_required
def index():
    if request.method != "POST":
        return render_template(
            "tasks/index.html", tasks=_visible_tasks(), task=None, task_types=TASK_TYPES
        )

    task = _read_form()
    try:
        scheduled_task_service.create_task(
            current_user.id, current_user.is_admin, task, get_audit_context()
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return render_template(
            "tasks/index.html", tasks=_visible_tasks(), task=task, task_types=TASK_TYPES
        )
    flash("Scheduled task created.", "success")
    return redirect(url_for("tasks.index"))


@login_required
def complete(task_id):
    _change_status(task_id, "completed")
    flash("Task marked complete.", "success")
    return redirect(url_for("tasks.index"))


@login_required
def cancel(task_id):
    _change_status(task_id, "cancelled")
    flash("Task cancelled.", "info")
    return redirect(url_for("tasks.index"))


def _visible_tasks(limit=None, status=None):
    return scheduled_task_repository.list_visible(
        current_user.id, current_user.is_admin, status=status, limit=limit
    )


def _read_form():
    scope = clean_text(request.form.get("scope")) or "personal"
    if not current_user.is_admin or scope not in {"admin", "global"}:
        scope = "personal"
    return {
        "title": clean_text(request.form.get("title")),
        "description": clean_text(request.form.get("description")),
        "task_type": clean_text(request.form.get("task_type")) or "general",
        "due_at": _parse_due_at(request.form.get("due_at")),
        "scope": scope,
        "user_id": None if scope in {"admin", "global"} else current_user.id,
    }


def _change_status(task_id, status):
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


def _parse_due_at(raw_value):
    raw_value = clean_text(raw_value)
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None
