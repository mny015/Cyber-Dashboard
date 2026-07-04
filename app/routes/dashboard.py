from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from utils.decorators import admin_required
from utils.db import fetch_all, fetch_one
from utils.performance import (
    get_admin_security_summary,
    get_user_performance,
    get_user_security_summary,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    return render_template("index.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    # Redirect to role-specific dashboard
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))
    return redirect(url_for("dashboard.user_dashboard"))


@dashboard_bp.route("/user/dashboard")
@login_required
def user_dashboard():
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))

    user_id = current_user.id
    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM topics
             WHERE owner_id = %s AND is_deleted = 0) AS topics,
            (SELECT COUNT(*) FROM notes
             WHERE owner_id = %s AND is_deleted = 0) AS notes,
            (SELECT COUNT(*) FROM categories
             WHERE owner_id = %s AND is_deleted = 0) AS categories,
            (SELECT COUNT(*) FROM lab_completions
             WHERE user_id = %s) AS completed_labs,
            (SELECT COUNT(*) FROM security_findings
             WHERE owner_id = %s AND is_deleted = 0) AS security_findings,
            (SELECT COUNT(*) FROM note_access_requests AS requests
             JOIN topics ON topics.id = requests.topic_id
             WHERE topics.owner_id = %s AND requests.status = 'pending') AS notifications
        """,
        (user_id, user_id, user_id, user_id, user_id, user_id),
    )
    recent_topics = fetch_all(
        """
        SELECT topics.id, topics.title, topics.status, topics.priority,
               topics.updated_at, categories.name AS category_name
        FROM topics
        LEFT JOIN categories ON categories.id = topics.category_id
        WHERE topics.owner_id = %s AND topics.is_deleted = 0
        ORDER BY topics.updated_at DESC
        LIMIT 5
        """,
        (user_id,),
    )
    available_labs = fetch_all(
        """
        SELECT labs.id, labs.name, platforms.name AS platform,
               labs.visibility, owners.display_name AS owner_name
        FROM lab_references AS labs
        JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
        JOIN users AS owners ON owners.id = labs.owner_id
        LEFT JOIN lab_completions AS completions
          ON completions.lab_id = labs.id AND completions.user_id = %s
        WHERE labs.is_deleted = 0
          AND completions.id IS NULL
          AND (labs.owner_id = %s OR labs.visibility = 'everyone')
        ORDER BY labs.updated_at DESC
        LIMIT 4
        """,
        (user_id, user_id),
    )
    return render_template(
        "user/dashboard.html",
        stats=stats,
        recent_topics=recent_topics,
        available_labs=available_labs,
        performance=get_user_performance(user_id),
        security_summary=get_user_security_summary(user_id),
    )


@dashboard_bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    admin_id = current_user.id
    stats = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM users WHERE is_banned = 0) AS active_users,
            (SELECT COUNT(*) FROM topics WHERE is_deleted = 0) AS topics,
            (SELECT COUNT(*) FROM lab_references
             WHERE is_deleted = 0 AND visibility = 'everyone') AS shared_labs,
            (SELECT COUNT(*) FROM security_findings
             WHERE is_deleted = 0) AS security_findings,
            (SELECT COUNT(*) FROM note_access_requests
             WHERE requester_admin_id = %s AND status = 'pending') AS pending_requests
        """,
        (admin_id,),
    )
    recent_activity = fetch_all(
        """
        SELECT audit_logs.action, audit_logs.details, audit_logs.created_at,
               users.display_name AS user_name
        FROM audit_logs
        LEFT JOIN users ON users.id = audit_logs.user_id
        ORDER BY audit_logs.created_at DESC
        LIMIT 6
        """
    )
    topic_statuses = fetch_all(
        """
        SELECT status, COUNT(*) AS total
        FROM topics
        WHERE is_deleted = 0
        GROUP BY status
        ORDER BY total DESC
        """
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_activity=recent_activity,
        topic_statuses=topic_statuses,
        security_summary=get_admin_security_summary(),
    )
