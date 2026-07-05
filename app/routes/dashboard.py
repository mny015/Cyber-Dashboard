from datetime import date, timedelta

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from pymysql.err import OperationalError, ProgrammingError

from utils.decorators import admin_required
from utils.db import fetch_all, fetch_one

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    return render_template("index.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))
    return redirect(url_for("dashboard.user_dashboard"))


@dashboard_bp.route("/user/dashboard")
@login_required
def user_dashboard():
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))

    user_id = current_user.id
    room_progress = get_user_room_progress(user_id)
    stats = get_user_dashboard_stats(user_id, room_progress)
    activity_bars = get_user_weekly_activity(user_id)
    changes_this_week = sum(item["count"] for item in activity_bars)

    return render_template(
        "user/dashboard.html",
        stats=stats,
        activity_bars=activity_bars,
        changes_this_week=changes_this_week,
        room_progress=room_progress,
        recent_changes=get_user_recent_changes(user_id),
        scheduled_tasks=get_user_scheduled_tasks(user_id),
        available_labs=get_user_scheduled_items(user_id),
        last_done_items=get_user_last_done_items(user_id),
    )


@dashboard_bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    stats = get_admin_dashboard_stats()
    shared_progress = get_admin_shared_lab_progress(stats)
    activity_bars = get_admin_weekly_activity()
    changes_this_week = sum(item["count"] for item in activity_bars)

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        activity_bars=activity_bars,
        changes_this_week=changes_this_week,
        shared_progress=shared_progress,
        platform_metrics=get_admin_platform_metrics(),
        pending_requests=get_admin_pending_requests(),
        recent_activity=get_admin_recent_activity(),
        shared_labs=get_admin_shared_labs(),
        scheduled_tasks=get_admin_scheduled_tasks(stats),
        last_done_items=get_admin_last_done_items(),
    )


def get_user_dashboard_stats(user_id, room_progress):
    row = fetch_one(
        """
        SELECT
            (SELECT COUNT(*)
             FROM topics
             WHERE owner_id = %s AND is_deleted = 0) AS topics,
            (SELECT COUNT(*)
             FROM notes
             WHERE owner_id = %s AND is_deleted = 0) AS notes,
            (SELECT COUNT(*)
             FROM notes
             WHERE owner_id = %s AND is_deleted = 0
               AND updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)) AS notes_this_week,
            (SELECT COUNT(*)
             FROM categories AS categories
             JOIN users AS owners ON owners.id = categories.owner_id
             WHERE categories.is_deleted = 0
               AND (categories.owner_id = %s OR owners.role = 'admin')) AS categories,
            (SELECT COUNT(*)
             FROM note_access_requests AS requests
             JOIN topics ON topics.id = requests.topic_id
             WHERE topics.owner_id = %s AND requests.status = 'pending') AS pending_requests,
            (SELECT COUNT(*)
             FROM security_findings
             WHERE owner_id = %s AND is_deleted = 0) AS security_findings
        """,
        (user_id, user_id, user_id, user_id, user_id, user_id),
    ) or {}
    stats = normalize_counts(row)
    stats["visible_labs"] = room_progress["total"]
    stats["completed_labs"] = room_progress["completed"]
    stats["notifications"] = stats["pending_requests"]
    stats["scheduled_tasks"] = count_user_scheduled_tasks(user_id)
    return stats


def get_user_room_progress(user_id):
    row = fetch_one(
        """
        SELECT
            (SELECT COUNT(*)
             FROM lab_references AS labs
             JOIN users AS owners ON owners.id = labs.owner_id
             WHERE labs.is_deleted = 0
               AND (labs.owner_id = %s OR (labs.visibility = 'public' AND owners.role = 'admin'))) AS total_rooms,
            (SELECT COUNT(DISTINCT completions.lab_id)
             FROM lab_completions AS completions
             JOIN lab_references AS labs ON labs.id = completions.lab_id
             JOIN users AS owners ON owners.id = labs.owner_id
             WHERE completions.user_id = %s
               AND labs.is_deleted = 0
               AND (labs.owner_id = %s OR (labs.visibility = 'public' AND owners.role = 'admin'))) AS completed_rooms
        """,
        (user_id, user_id, user_id),
    ) or {}
    total = int(row.get("total_rooms") or 0)
    completed = int(row.get("completed_rooms") or 0)
    percent = round((completed / total) * 100) if total else 0
    return {"total": total, "completed": completed, "percent": percent}


def get_user_weekly_activity(user_id):
    rows = safe_fetch_all(
        """
        SELECT DATE(activity.event_at) AS activity_day, COUNT(*) AS total
        FROM (
            SELECT updated_at AS event_at
            FROM notes
            WHERE owner_id = %s AND is_deleted = 0
              AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT updated_at AS event_at
            FROM topics
            WHERE owner_id = %s AND is_deleted = 0
              AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT updated_at AS event_at
            FROM categories
            WHERE owner_id = %s AND is_deleted = 0
              AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT completed_at AS event_at
            FROM lab_completions
            WHERE user_id = %s
              AND completed_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT updated_at AS event_at
            FROM security_findings
            WHERE owner_id = %s AND is_deleted = 0
              AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT updated_at AS event_at
            FROM scheduled_tasks
            WHERE user_id = %s
              AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
        ) AS activity
        GROUP BY DATE(activity.event_at)
        ORDER BY activity_day
        """,
        (user_id, user_id, user_id, user_id, user_id, user_id),
    )
    return build_week_bars(rows, "activity_day")


def get_user_recent_changes(user_id):
    return safe_fetch_all(
        """
        SELECT *
        FROM (
            SELECT 'Topic' AS item_type, title, status AS detail, updated_at AS changed_at
            FROM topics
            WHERE owner_id = %s AND is_deleted = 0
            UNION ALL
            SELECT 'Note' AS item_type, title, 'Updated' AS detail, updated_at AS changed_at
            FROM notes
            WHERE owner_id = %s AND is_deleted = 0
            UNION ALL
            SELECT 'Category' AS item_type, name AS title, 'Updated' AS detail, updated_at AS changed_at
            FROM categories
            WHERE owner_id = %s AND is_deleted = 0
            UNION ALL
            SELECT 'Room completed' AS item_type, labs.name AS title, platforms.name AS detail,
                   completions.completed_at AS changed_at
            FROM lab_completions AS completions
            JOIN lab_references AS labs ON labs.id = completions.lab_id
            JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
            WHERE completions.user_id = %s AND labs.is_deleted = 0
            UNION ALL
            SELECT 'Finding' AS item_type, title, status AS detail, updated_at AS changed_at
            FROM security_findings
            WHERE owner_id = %s AND is_deleted = 0
            UNION ALL
            SELECT 'Task' AS item_type, title, status AS detail, updated_at AS changed_at
            FROM scheduled_tasks
            WHERE user_id = %s
        ) AS changes
        ORDER BY changed_at DESC
        LIMIT 6
        """,
        (user_id, user_id, user_id, user_id, user_id, user_id),
    )


def get_user_scheduled_items(user_id):
    return safe_fetch_all(
        """
        SELECT labs.id, labs.name AS title, platforms.name AS detail,
               owners.display_name AS owner_name, labs.visibility, labs.updated_at
        FROM lab_references AS labs
        JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
        JOIN users AS owners ON owners.id = labs.owner_id
        LEFT JOIN lab_completions AS completions
          ON completions.lab_id = labs.id AND completions.user_id = %s
        WHERE labs.is_deleted = 0
          AND completions.id IS NULL
          AND (labs.owner_id = %s OR (labs.visibility = 'public' AND owners.role = 'admin'))
        ORDER BY labs.updated_at DESC
        LIMIT 3
        """,
        (user_id, user_id),
    )


def get_user_scheduled_tasks(user_id):
    return safe_fetch_all(
        """
        SELECT scheduled_tasks.*, creators.display_name AS creator_name
        FROM scheduled_tasks
        JOIN users AS creators ON creators.id = scheduled_tasks.created_by
        WHERE scheduled_tasks.status = 'upcoming'
          AND (
                scheduled_tasks.user_id = %s
             OR scheduled_tasks.scope IN ('admin', 'global')
          )
        ORDER BY scheduled_tasks.due_at IS NULL ASC,
                 scheduled_tasks.due_at ASC,
                 scheduled_tasks.updated_at DESC
        LIMIT 3
        """,
        (user_id,),
    )


def count_user_scheduled_tasks(user_id):
    row = safe_fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM scheduled_tasks
        WHERE status = 'upcoming'
          AND (user_id = %s OR scope IN ('admin', 'global'))
        """,
        (user_id,),
    ) or {}
    return int(row.get("total") or 0)


def get_user_last_done_items(user_id):
    return safe_fetch_all(
        """
        SELECT *
        FROM (
            SELECT labs.name AS title, platforms.name AS detail, 'Completed' AS badge,
                   completions.completed_at AS done_at
            FROM lab_completions AS completions
            JOIN lab_references AS labs ON labs.id = completions.lab_id
            JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
            WHERE completions.user_id = %s AND labs.is_deleted = 0
            UNION ALL
            SELECT REPLACE(audit_logs.action, '_', ' ') AS title, audit_logs.details AS detail,
                   'Completed' AS badge, audit_logs.created_at AS done_at
            FROM audit_logs
            WHERE audit_logs.user_id = %s
            UNION ALL
            SELECT title, COALESCE(description, 'Scheduled task completed') AS detail,
                   'Completed' AS badge, updated_at AS done_at
            FROM scheduled_tasks
            WHERE user_id = %s AND status = 'completed'
        ) AS completed_items
        ORDER BY done_at DESC
        LIMIT 3
        """,
        (user_id, user_id, user_id),
    )


def get_admin_dashboard_stats():
    row = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM users) AS total_users,
            (SELECT COUNT(*) FROM users WHERE is_banned = 0) AS active_users,
            (SELECT COUNT(*) FROM users WHERE is_banned = 1) AS banned_users,
            (SELECT COUNT(*) FROM users WHERE role = 'admin') AS admin_users,
            (SELECT COUNT(*) FROM topics WHERE is_deleted = 0) AS total_topics,
            (SELECT COUNT(*) FROM notes WHERE is_deleted = 0) AS total_notes,
            (SELECT COUNT(*) FROM categories WHERE is_deleted = 0) AS total_categories,
            (SELECT COUNT(*) FROM lab_references WHERE is_deleted = 0) AS total_labs,
            (SELECT COUNT(*) FROM lab_references
             WHERE is_deleted = 0 AND visibility = 'public') AS shared_labs,
            (SELECT COUNT(*) FROM note_access_requests
             WHERE status = 'pending') AS pending_requests,
            (SELECT COUNT(*) FROM audit_logs
             WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)) AS audit_events_week,
            (SELECT COUNT(*) FROM audit_logs
             WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
               AND (action LIKE %s OR action LIKE %s)) AS backup_exports_week
        """,
        ("%backup%", "%export%"),
    ) or {}
    return normalize_counts(row)


def get_admin_shared_lab_progress(stats):
    total = int(stats.get("total_labs") or 0)
    shared = int(stats.get("shared_labs") or 0)
    percent = round((shared / total) * 100) if total else 0
    return {"total": total, "shared": shared, "percent": percent}


def get_admin_weekly_activity():
    rows = safe_fetch_all(
        """
        SELECT DATE(activity.event_at) AS activity_day, COUNT(*) AS total
        FROM (
            SELECT created_at AS event_at
            FROM users
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT created_at AS event_at
            FROM topics
            WHERE is_deleted = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT created_at AS event_at
            FROM notes
            WHERE is_deleted = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT created_at AS event_at
            FROM categories
            WHERE is_deleted = 0 AND created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT updated_at AS event_at
            FROM lab_references
            WHERE is_deleted = 0 AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT COALESCE(responded_at, requested_at) AS event_at
            FROM note_access_requests
            WHERE COALESCE(responded_at, requested_at) >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT audit_logs.created_at AS event_at
            FROM audit_logs
            JOIN users ON users.id = audit_logs.user_id
            WHERE users.role = 'admin'
              AND audit_logs.created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
            UNION ALL
            SELECT updated_at AS event_at
            FROM scheduled_tasks
            WHERE scope IN ('admin', 'global')
              AND updated_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
        ) AS activity
        GROUP BY DATE(activity.event_at)
        ORDER BY activity_day
        """
    )
    return build_week_bars(rows, "activity_day")


def get_admin_platform_metrics():
    return fetch_all(
        """
        SELECT platforms.name,
               COUNT(DISTINCT labs.id) AS total_labs,
               COUNT(DISTINCT CASE WHEN labs.visibility = 'public' THEN labs.id END) AS shared_labs,
               COUNT(completions.id) AS completions
        FROM lab_platforms AS platforms
        LEFT JOIN lab_references AS labs
          ON labs.platform_id = platforms.id AND labs.is_deleted = 0
        LEFT JOIN lab_completions AS completions ON completions.lab_id = labs.id
        GROUP BY platforms.id, platforms.name
        ORDER BY total_labs DESC, platforms.name ASC
        LIMIT 5
        """
    )


def get_admin_pending_requests():
    return fetch_all(
        """
        SELECT requests.id, topics.title AS topic_title, owners.display_name AS owner_name,
               requests.requested_at
        FROM note_access_requests AS requests
        JOIN topics ON topics.id = requests.topic_id
        JOIN users AS owners ON owners.id = topics.owner_id
        WHERE requests.status = 'pending'
        ORDER BY requests.requested_at DESC
        LIMIT 3
        """
    )


def get_admin_recent_activity():
    return fetch_all(
        """
        SELECT audit_logs.action, audit_logs.details, audit_logs.created_at,
               users.display_name AS user_name
        FROM audit_logs
        LEFT JOIN users ON users.id = audit_logs.user_id
        ORDER BY audit_logs.created_at DESC
        LIMIT 5
        """
    )


def get_admin_shared_labs():
    return fetch_all(
        """
        SELECT labs.name, platforms.name AS platform_name, owners.display_name AS owner_name,
               COUNT(completions.id) AS completion_count, labs.updated_at
        FROM lab_references AS labs
        JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
        JOIN users AS owners ON owners.id = labs.owner_id
        LEFT JOIN lab_completions AS completions ON completions.lab_id = labs.id
        WHERE labs.is_deleted = 0 AND labs.visibility = 'public'
        GROUP BY labs.id, labs.name, platforms.name, owners.display_name, labs.updated_at
        ORDER BY labs.updated_at DESC
        LIMIT 5
        """
    )


def get_admin_scheduled_tasks(stats):
    tasks = safe_fetch_all(
        """
        SELECT scheduled_tasks.*, creators.display_name AS creator_name
        FROM scheduled_tasks
        JOIN users AS creators ON creators.id = scheduled_tasks.created_by
        WHERE scheduled_tasks.status = 'upcoming'
          AND scheduled_tasks.scope IN ('admin', 'global')
        ORDER BY scheduled_tasks.due_at IS NULL ASC,
                 scheduled_tasks.due_at ASC,
                 scheduled_tasks.updated_at DESC
        LIMIT 4
        """
    )
    if tasks:
        return tasks

    return [
        {
            "title": "Review note access requests",
            "detail": f"{stats.get('pending_requests', 0)} pending requests",
            "task_type": "review",
            "scope": "admin",
            "status": "upcoming",
            "due_at": None,
            "url": url_for("admin.note_requests"),
        },
        {
            "title": "Verify shared lab visibility",
            "detail": f"{stats.get('shared_labs', 0)} rooms shared with users",
            "task_type": "lab",
            "scope": "admin",
            "status": "upcoming",
            "due_at": None,
            "url": url_for("labs.index"),
        },
        {
            "title": "Backup/export data",
            "detail": f"{stats.get('backup_exports_week', 0)} exports this week",
            "task_type": "backup",
            "scope": "admin",
            "status": "upcoming",
            "due_at": None,
            "url": url_for("backup.index"),
        },
    ]


def get_admin_last_done_items():
    return fetch_all(
        """
        SELECT audit_logs.action AS title, audit_logs.details AS detail,
               'Completed' AS badge, audit_logs.created_at AS done_at,
               users.display_name AS user_name
        FROM audit_logs
        LEFT JOIN users ON users.id = audit_logs.user_id
        WHERE users.role = 'admin'
           OR audit_logs.action IN (
                'note_access_approved',
                'note_access_denied',
                'lab_created',
                'lab_updated',
                'user_banned',
                'user_unbanned',
                'admin_backup_exported'
           )
        ORDER BY audit_logs.created_at DESC
        LIMIT 3
        """
    )


def normalize_counts(row):
    return {key: int(value or 0) for key, value in row.items()}


def build_week_bars(rows, day_key):
    today = date.today()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    counts_by_day = {normalize_day(row[day_key]): int(row["total"] or 0) for row in rows}
    max_count = max([counts_by_day.get(day, 0) for day in days] + [1])

    return [
        {
            "label": day.strftime("%a"),
            "count": counts_by_day.get(day, 0),
            "height": round((counts_by_day.get(day, 0) / max_count) * 100) if counts_by_day.get(day, 0) else 0,
        }
        for day in days
    ]


def normalize_day(value):
    if hasattr(value, "date"):
        return value.date()
    return value


def safe_fetch_all(query, params=None):
    try:
        return fetch_all(query, params)
    except (OperationalError, ProgrammingError) as error:
        if getattr(error, "args", [None])[0] in {1054, 1146}:
            return []
        raise


def safe_fetch_one(query, params=None):
    rows = safe_fetch_all(query, params)
    return rows[0] if rows else None
