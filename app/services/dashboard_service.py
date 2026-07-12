"""Assemble dashboard view data from complex reporting repositories."""

from datetime import date, timedelta

from app.repositories import dashboard_repository


def user_dashboard_data(user_id):
    room_progress = _user_room_progress(user_id)
    stats = _normalize_counts(dashboard_repository.user_metrics(user_id))
    stats.update(
        {
            "visible_labs": room_progress["total"],
            "completed_labs": room_progress["completed"],
            "notifications": stats["pending_requests"],
            "scheduled_tasks": dashboard_repository.user_scheduled_task_count(user_id),
        }
    )
    activity_bars = _week_bars(
        dashboard_repository.user_weekly_activity(user_id), "activity_day"
    )
    return {
        "stats": stats,
        "activity_bars": activity_bars,
        "changes_this_week": sum(item["count"] for item in activity_bars),
        "room_progress": room_progress,
        "recent_changes": dashboard_repository.user_recent_changes(user_id),
        "scheduled_tasks": dashboard_repository.user_scheduled_tasks(user_id),
        "available_labs": dashboard_repository.user_scheduled_labs(user_id),
        "last_done_items": dashboard_repository.user_last_done(user_id),
    }


def admin_dashboard_data():
    stats = _normalize_counts(dashboard_repository.admin_metrics())
    activity_bars = _week_bars(
        dashboard_repository.admin_weekly_activity(), "activity_day"
    )
    total_labs = int(stats.get("total_labs") or 0)
    shared_labs = int(stats.get("shared_labs") or 0)
    return {
        "stats": stats,
        "activity_bars": activity_bars,
        "changes_this_week": sum(item["count"] for item in activity_bars),
        "shared_progress": {
            "total": total_labs,
            "shared": shared_labs,
            "percent": round((shared_labs / total_labs) * 100) if total_labs else 0,
        },
        "platform_metrics": dashboard_repository.admin_platform_metrics(),
        "pending_requests": dashboard_repository.admin_pending_requests(),
        "recent_activity": dashboard_repository.admin_recent_activity(),
        "shared_labs": dashboard_repository.admin_shared_labs(),
        "scheduled_tasks": dashboard_repository.admin_scheduled_tasks(),
        "last_done_items": dashboard_repository.admin_last_done(),
    }


def _user_room_progress(user_id):
    row = dashboard_repository.user_room_progress(user_id)
    total = int(row.get("total_rooms") or 0)
    completed = int(row.get("completed_rooms") or 0)
    return {
        "total": total,
        "completed": completed,
        "percent": round((completed / total) * 100) if total else 0,
    }


def _normalize_counts(row):
    return {key: int(value or 0) for key, value in row.items()}


def _week_bars(rows, day_key):
    today = date.today()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    counts = {_normalize_day(row[day_key]): int(row["total"] or 0) for row in rows}
    maximum = max([counts.get(day, 0) for day in days] + [1])
    return [
        {
            "label": day.strftime("%a"),
            "count": counts.get(day, 0),
            "height": round((counts.get(day, 0) / maximum) * 100)
            if counts.get(day, 0)
            else 0,
        }
        for day in days
    ]


def _normalize_day(value):
    return value.date() if hasattr(value, "date") else value
