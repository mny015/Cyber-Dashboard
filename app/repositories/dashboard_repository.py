"""Complex read-only dashboard reports backed by named SQL."""

from app.models import AuditLog, LabReference, NoteAccessRequest, ScheduledTask
from app.utils.database import db


def user_metrics(user_id):
    return db.named_query(
        "user_dashboard_metrics", {"user_id": int(user_id)}, fetch="one"
    ) or {}


def user_room_progress(user_id):
    return db.named_query(
        "user_room_progress", {"user_id": int(user_id)}, fetch="one"
    ) or {}


def user_weekly_activity(user_id):
    return db.named_query("user_weekly_activity", {"user_id": int(user_id)})


def user_recent_changes(user_id):
    return db.named_query("user_recent_changes", {"user_id": int(user_id)})


def user_scheduled_labs(user_id):
    rows = db.named_query("user_scheduled_labs", {"user_id": int(user_id)})
    return LabReference.from_rows(rows)


def user_scheduled_tasks(user_id):
    rows = db.named_query("user_dashboard_tasks", {"user_id": int(user_id)})
    return ScheduledTask.from_rows(rows)


def user_scheduled_task_count(user_id):
    row = db.named_query(
        "user_dashboard_task_count", {"user_id": int(user_id)}, fetch="one"
    ) or {}
    return int(row.get("total") or 0)


def user_last_done(user_id):
    return db.named_query("user_last_done", {"user_id": int(user_id)})


def admin_metrics():
    return db.named_query(
        "admin_dashboard_metrics",
        {"backup_pattern": "%backup%", "export_pattern": "%export%"},
        fetch="one",
    ) or {}


def admin_weekly_activity():
    return db.named_query("admin_weekly_activity")


def admin_platform_metrics():
    return db.named_query("admin_platform_metrics")


def admin_pending_requests():
    return NoteAccessRequest.from_rows(db.named_query("admin_pending_note_requests"))


def admin_recent_activity():
    return AuditLog.from_rows(db.named_query("admin_recent_activity"))


def admin_shared_labs():
    return LabReference.from_rows(db.named_query("admin_shared_labs"))


def admin_scheduled_tasks():
    return ScheduledTask.from_rows(db.named_query("admin_dashboard_tasks"))


def admin_last_done():
    return db.named_query("admin_last_done")
