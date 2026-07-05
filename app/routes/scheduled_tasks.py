from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from utils.audit import log_audit
from utils.db import execute, fetch_all, fetch_one
from utils.helpers import clean_text

tasks_bp = Blueprint("tasks", __name__, url_prefix="/scheduled-tasks")

TASK_TYPES = ("general", "lab", "note", "backup", "review", "roadmap")
TASK_STATUSES = ("upcoming", "completed", "cancelled")
TASK_SCOPES = ("personal", "admin", "global")


@tasks_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        task = read_task_form()
        error = validate_task(task)
        if error:
            flash(error, "danger")
            return render_template("tasks/index.html", tasks=get_visible_tasks(), task=task, task_types=TASK_TYPES)

        execute(
            """
            INSERT INTO scheduled_tasks
                (user_id, created_by, title, description, task_type, due_at,
                 status, scope, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'upcoming', %s, NOW(), NOW())
            """,
            (
                task["user_id"],
                current_user.id,
                task["title"],
                task["description"],
                task["task_type"],
                task["due_at"],
                task["scope"],
            ),
        )
        log_audit("scheduled_task_created", f"Created scheduled task {task['title']}")
        flash("Scheduled task created.", "success")
        return redirect(url_for("tasks.index"))

    return render_template("tasks/index.html", tasks=get_visible_tasks(), task=None, task_types=TASK_TYPES)


@tasks_bp.route("/<int:task_id>/complete", methods=["POST"])
@login_required
def complete(task_id):
    task = get_manageable_task_or_404(task_id)
    execute(
        """
        UPDATE scheduled_tasks
        SET status = 'completed', updated_at = NOW()
        WHERE id = %s
        """,
        (task["id"],),
    )
    log_audit("scheduled_task_completed", f"Completed scheduled task {task['title']}")
    flash("Task marked complete.", "success")
    return redirect(url_for("tasks.index"))


@tasks_bp.route("/<int:task_id>/cancel", methods=["POST"])
@login_required
def cancel(task_id):
    task = get_manageable_task_or_404(task_id)
    execute(
        """
        UPDATE scheduled_tasks
        SET status = 'cancelled', updated_at = NOW()
        WHERE id = %s
        """,
        (task["id"],),
    )
    log_audit("scheduled_task_cancelled", f"Cancelled scheduled task {task['title']}")
    flash("Task cancelled.", "info")
    return redirect(url_for("tasks.index"))


def get_visible_tasks(limit=None, status=None):
    params = []
    status_clause = ""
    if status:
        status_clause = "AND scheduled_tasks.status = %s"
        params.append(status)

    if current_user.is_admin:
        visibility_clause = """
          AND (
                scheduled_tasks.created_by = %s
             OR scheduled_tasks.scope IN ('admin', 'global')
             OR scheduled_tasks.user_id = %s
          )
        """
        params.extend([current_user.id, current_user.id])
    else:
        visibility_clause = """
          AND (
                scheduled_tasks.user_id = %s
             OR (scheduled_tasks.scope IN ('admin', 'global') AND scheduled_tasks.status = 'upcoming')
          )
        """
        params.append(current_user.id)

    limit_clause = ""
    if limit:
        limit_clause = "LIMIT %s"
        params.append(limit)

    return fetch_all(
        f"""
        SELECT scheduled_tasks.*, creators.display_name AS creator_name,
               assignees.display_name AS assignee_name
        FROM scheduled_tasks
        JOIN users AS creators ON creators.id = scheduled_tasks.created_by
        LEFT JOIN users AS assignees ON assignees.id = scheduled_tasks.user_id
        WHERE 1 = 1
          {status_clause}
          {visibility_clause}
        ORDER BY
          scheduled_tasks.status = 'upcoming' DESC,
          scheduled_tasks.due_at IS NULL ASC,
          scheduled_tasks.due_at ASC,
          scheduled_tasks.updated_at DESC
        {limit_clause}
        """,
        tuple(params),
    )


def get_manageable_task_or_404(task_id):
    task = fetch_one(
        """
        SELECT *
        FROM scheduled_tasks
        WHERE id = %s
        """,
        (task_id,),
    )
    if not task:
        abort(404)

    if current_user.is_admin and (task["created_by"] == current_user.id or task["scope"] in {"admin", "global"}):
        return task
    if task["user_id"] == current_user.id and task["scope"] == "personal":
        return task

    abort(403)


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


def validate_task(task):
    if not task["title"]:
        return "Task title is required."
    if task["task_type"] not in TASK_TYPES:
        return "Choose a valid task type."
    if task["scope"] not in TASK_SCOPES:
        return "Choose a valid task scope."
    return None


def parse_due_at(raw_value):
    raw_value = clean_text(raw_value)
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None
