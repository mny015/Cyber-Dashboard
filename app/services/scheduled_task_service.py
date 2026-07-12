"""Scheduled-task creation and state transition workflows."""

from app.models import ScheduledTask
from app.repositories import scheduled_task_repository
from app.services import audit_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.utils.database import db, transaction


TASK_TYPES = ("general", "lab", "note", "backup", "review", "roadmap")
TASK_STATUSES = ("upcoming", "completed", "cancelled")
TASK_SCOPES = ("personal", "admin", "global")


def create_task(actor_id, is_admin, task_data, context):
    title = task_data.get("title")
    task_type = task_data.get("task_type", "general")
    scope = task_data.get("scope", "personal")
    if not title:
        raise ValidationError("Task title is required.")
    if task_type not in TASK_TYPES:
        raise ValidationError("Choose a valid task type.")
    if scope not in TASK_SCOPES:
        raise ValidationError("Choose a valid task scope.")
    if not is_admin or scope not in {"admin", "global"}:
        scope = "personal"

    task = ScheduledTask(
        user_id=None if scope in {"admin", "global"} else actor_id,
        created_by=actor_id,
        title=title,
        description=task_data.get("description"),
        task_type=task_type,
        due_at=task_data.get("due_at"),
        status="upcoming",
        scope=scope,
    )
    with transaction() as cursor:
        database = db.using(cursor)
        scheduled_task_repository.create(task, database=database)
        audit_service.record(
            "scheduled_task_created",
            f"Created scheduled task {task.title}",
            context,
            database,
        )
    return task


def set_status(task_id, actor_id, is_admin, status, context):
    if status not in {"completed", "cancelled"}:
        raise ValidationError("Choose a valid task status.")
    access = scheduled_task_repository.find_manageable(task_id, actor_id, is_admin)
    if not access.task:
        raise NotFoundError("Scheduled task not found.")
    if not access.can_manage:
        raise PermissionDeniedError("This scheduled task cannot be changed by this user.")

    with transaction() as cursor:
        affected = scheduled_task_repository.set_status_manageable(
            task_id, actor_id, is_admin, status, cursor=cursor
        )
        if not affected:
            raise PermissionDeniedError("The scheduled task is no longer manageable.")
        action = f"scheduled_task_{status}"
        audit_service.record(
            action,
            f"{status.title()} scheduled task {access.task.title}",
            context,
            db.using(cursor),
        )
    return access.task
