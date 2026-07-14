"""HTTP handlers for public, user, and administrator dashboards."""

from flask import redirect, render_template, url_for
from flask_login import current_user, login_required

from app.services import dashboard_service
from app.utils.decorators import admin_required


def index():
    return render_template("index.html")


@login_required
def dashboard():
    endpoint = (
        "dashboard.admin_dashboard"
        if getattr(current_user, "is_admin", False)
        else "dashboard.user_dashboard"
    )
    return redirect(url_for(endpoint))


@login_required
def user_dashboard():
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))
    return render_template(
        "user/dashboard.html", **dashboard_service.user_dashboard_data(current_user.id)
    )


@login_required
@admin_required
def admin_dashboard():
    data = dashboard_service.admin_dashboard_data()
    if not data["scheduled_tasks"]:
        data["scheduled_tasks"] = _default_admin_tasks(data["stats"])
    return render_template("admin/dashboard.html", **data)


def _default_admin_tasks(stats):
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
