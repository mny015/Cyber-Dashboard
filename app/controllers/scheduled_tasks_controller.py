"""HTTP handlers for scheduled task management."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import validate_action
from app.forms.scheduled_tasks import ScheduledTaskForm
from app.repositories import scheduled_task_repository
from app.services import scheduled_task_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.utils.audit import get_audit_context

TASK_TYPES = scheduled_task_service.TASK_TYPES


@login_required
def index():
    form = _task_form()
    if not form.validate_on_submit():
        return _render_index(form)

    task = {
        "title": form.title.data,
        "description": form.description.data or "",
        "task_type": form.task_type.data,
        "due_at": form.due_at.data,
        "scope": form.scope.data,
        "user_id": None if form.scope.data in {"admin", "global"} else current_user.id,
    }
    try:
        scheduled_task_service.create_task(
            current_user.id, current_user.is_admin, task, get_audit_context()
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return _render_index(form)
    flash("Task added to your schedule.", "success")
    return redirect(url_for("tasks.index"))


@login_required
def complete(task_id):
    if not validate_action():
        return redirect(url_for("tasks.index"))
    _change_status(task_id, "completed")
    flash("Task marked as complete.", "success")
    return redirect(url_for("tasks.index"))


@login_required
def cancel(task_id):
    if not validate_action():
        return redirect(url_for("tasks.index"))
    _change_status(task_id, "cancelled")
    flash("Task removed from the schedule.", "info")
    return redirect(url_for("tasks.index"))


def _visible_tasks(limit=None, status=None):
    return scheduled_task_repository.list_visible(
        current_user.id, current_user.is_admin, status=status, limit=limit
    )


def _task_form():
    form = ScheduledTaskForm()
    form.task_type.choices = [(value, value.title()) for value in TASK_TYPES]
    form.scope.choices = [("personal", "Personal")]
    if current_user.is_admin:
        form.scope.choices.extend([("admin", "Admin"), ("global", "Global")])
    return form


def _render_index(form):
    return render_template(
        "tasks/index.html",
        tasks=_visible_tasks(),
        task=None,
        task_types=TASK_TYPES,
        form=form,
    )


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
