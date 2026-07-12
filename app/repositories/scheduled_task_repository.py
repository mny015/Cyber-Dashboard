"""Scheduled task persistence with role-aware visibility and mutation scopes."""

from dataclasses import dataclass
from datetime import datetime

from app.models import ScheduledTask
from app.utils.database import db, transaction


@dataclass(frozen=True, slots=True)
class TaskAccess:
    task: ScheduledTask | None
    can_manage: bool


def list_visible(user_id, is_admin, status=None, limit=None):
    rows = db.named_query(
        "scheduled_tasks_visible",
        {"user_id": int(user_id), "is_admin": bool(is_admin), "status": status},
    )
    tasks = ScheduledTask.from_rows(rows)
    return tasks[:limit] if limit else tasks


def find_manageable(task_id, user_id, is_admin):
    row = db.named_query(
        "manageable_scheduled_task",
        {"task_id": int(task_id), "user_id": int(user_id), "is_admin": bool(is_admin)},
        fetch="one",
    )
    return TaskAccess(
        task=ScheduledTask.from_row(row),
        can_manage=bool(row and row.get("can_manage")),
    )


def create(task, database=None):
    database = database or db
    now = datetime.now()
    result = database.table(ScheduledTask.TABLE_NAME).insert(
        {
            "user_id": task.user_id,
            "created_by": task.created_by,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "due_at": task.due_at,
            "status": task.status,
            "scope": task.scope,
            "created_at": now,
            "updated_at": now,
        }
    )
    task.id = result.last_insert_id
    return task


def set_status_manageable(task_id, user_id, is_admin, status, cursor=None):
    """Update only when the actor still satisfies the task permission predicate."""
    if cursor is not None:
        return _set_status(cursor, task_id, user_id, is_admin, status)
    with transaction() as transaction_cursor:
        return _set_status(transaction_cursor, task_id, user_id, is_admin, status)


def _set_status(cursor, task_id, user_id, is_admin, status):
    cursor.execute(
            """
            UPDATE scheduled_tasks
            SET status = %s, updated_at = NOW()
            WHERE id = %s
              AND (
                    (%s = 1 AND (created_by = %s OR scope IN ('admin', 'global')))
                 OR (%s = 0 AND user_id = %s AND scope = 'personal')
              )
            """,
            (status, int(task_id), bool(is_admin), int(user_id), bool(is_admin), int(user_id)),
    )
    return cursor.rowcount
