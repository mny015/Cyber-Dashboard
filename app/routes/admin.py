from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from app.forms.admin import AdminPasswordResetForm, RoleForm
from app.models import AuditLog, Category, NoteAccessRequest, Topic, User
from utils.audit import log_audit
from utils.decorators import admin_required
from utils.db import execute, fetch_all, fetch_one, get_connection

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users_list = [User.from_row(row) for row in fetch_all("SELECT * FROM users ORDER BY created_at DESC")]
    return render_template("admin/users.html", users=users_list)


@admin_bp.route("/topics")
@login_required
@admin_required
def topic_summaries():
    rows = fetch_all(
        """
        SELECT topics.id, topics.title, topics.status, topics.priority, topics.updated_at,
               categories.name AS category_name,
               users.display_name AS owner_name,
               users.email AS owner_email
        FROM topics
        JOIN users ON users.id = topics.owner_id
        LEFT JOIN categories ON categories.id = topics.category_id
        WHERE topics.is_deleted = 0
        ORDER BY topics.updated_at DESC
        """
    )
    return render_template("admin/topic_summaries.html", topics=Topic.from_rows(rows))


@admin_bp.route("/topics/<int:topic_id>/request-notes", methods=["POST"])
@login_required
@admin_required
def request_topic_notes(topic_id):
    topic = fetch_one(
        """
        SELECT id, owner_id, title
        FROM topics
        WHERE id = %s AND is_deleted = 0
        """,
        (topic_id,),
    )
    if not topic:
        abort(404)
    if topic["owner_id"] == current_user.id:
        flash("You already own this topic.", "info")
        return redirect(url_for("admin.topic_summaries"))

    existing = fetch_one(
        """
        SELECT id, status
        FROM note_access_requests
        WHERE topic_id = %s AND requester_admin_id = %s
          AND status IN ('pending', 'approved')
        ORDER BY requested_at DESC
        LIMIT 1
        """,
        (topic_id, current_user.id),
    )
    if existing:
        flash(f"A {existing['status']} request already exists for this topic.", "warning")
        return redirect(url_for("admin.note_requests"))

    execute(
        """
        INSERT INTO note_access_requests
            (topic_id, note_id, requester_admin_id, status, requested_at, responded_at)
        VALUES (%s, NULL, %s, 'pending', NOW(), NULL)
        """,
        (topic_id, current_user.id),
    )
    log_audit("note_access_requested", f"Requested notes for topic {topic['title']}")
    flash("Note access request sent to the user.", "success")
    return redirect(url_for("admin.note_requests"))


@admin_bp.route("/note-requests")
@login_required
@admin_required
def note_requests():
    requests = fetch_all(
        """
        SELECT note_access_requests.*, topics.title AS topic_title,
               owners.display_name AS owner_name, owners.email AS owner_email,
               notes.title AS note_title
        FROM note_access_requests
        JOIN topics ON topics.id = note_access_requests.topic_id
        JOIN users AS owners ON owners.id = topics.owner_id
        LEFT JOIN notes ON notes.id = note_access_requests.note_id
        WHERE note_access_requests.requester_admin_id = %s
        ORDER BY note_access_requests.requested_at DESC
        """,
        (current_user.id,),
    )
    return render_template(
        "admin/note_requests.html",
        requests=NoteAccessRequest.from_rows(requests),
    )


@admin_bp.route("/note-requests/<int:request_id>/note")
@login_required
@admin_required
def approved_note(request_id):
    note = fetch_one(
        """
        SELECT note_access_requests.id AS request_id,
               notes.title, notes.body, notes.updated_at,
               topics.title AS topic_title,
               owners.display_name AS owner_name, owners.email AS owner_email
        FROM note_access_requests
        JOIN notes ON notes.id = note_access_requests.note_id
        JOIN topics ON topics.id = note_access_requests.topic_id
        JOIN users AS owners ON owners.id = topics.owner_id
        WHERE note_access_requests.id = %s
          AND note_access_requests.requester_admin_id = %s
          AND note_access_requests.status = 'approved'
          AND notes.is_deleted = 0
        """,
        (request_id, current_user.id),
    )
    if not note:
        abort(404)
    return render_template("admin/approved_note.html", note=note)


@admin_bp.route("/categories")
@login_required
@admin_required
def category_summaries():
    rows = fetch_all(
        """
        SELECT categories.id, categories.name, categories.color, categories.updated_at,
               users.display_name AS owner_name,
               users.email AS owner_email,
               COUNT(topics.id) AS topic_count
        FROM categories
        JOIN users ON users.id = categories.owner_id
        LEFT JOIN topics ON topics.category_id = categories.id AND topics.is_deleted = 0
        WHERE categories.is_deleted = 0
        GROUP BY categories.id, categories.name, categories.color, categories.updated_at,
                 users.display_name, users.email
        ORDER BY categories.updated_at DESC
        """
    )
    return render_template("admin/category_summaries.html", categories=Category.from_rows(rows))


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@admin_required
def update_role(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("admin.users"))
    form = RoleForm()
    if form.validate_on_submit():
        if user.id == current_user.id:
            flash("Use another administrator account to change your own role.", "danger")
            return redirect(url_for("admin.users"))
        if user.is_admin and form.role.data != "admin" and is_last_active_admin(user.id):
            flash("Keep at least one active administrator account.", "danger")
            return redirect(url_for("admin.users"))
        user.role = form.role.data
        execute("UPDATE users SET role = %s, updated_at = NOW() WHERE id = %s", (user.role, user.id))
        log_audit("role_updated", f"{user.email} role changed to {user.role}")
        flash("User role updated.", "success")
    else:
        flash("Choose a valid role.", "danger")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@login_required
@admin_required
def ban_user(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("You cannot ban your own account.", "danger")
        return redirect(url_for("admin.users"))
    if user.is_admin and is_last_active_admin(user.id):
        flash("Keep at least one active administrator account.", "danger")
        return redirect(url_for("admin.users"))

    user.is_banned = True
    execute("UPDATE users SET is_banned = 1, updated_at = NOW() WHERE id = %s", (user.id,))
    log_audit("user_banned", f"{user.email} was banned")
    flash("User banned.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@login_required
@admin_required
def unban_user(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        return redirect(url_for("admin.users"))
    user.is_banned = False
    execute("UPDATE users SET is_banned = 0, updated_at = NOW() WHERE id = %s", (user.id,))
    log_audit("user_unbanned", f"{user.email} was unbanned")
    flash("User unbanned.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/password", methods=["POST"])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("Use your own Security page to change your password.", "danger")
        return redirect(url_for("admin.users"))

    form = AdminPasswordResetForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("admin.users"))

    password_hash = generate_password_hash(form.password.data)
    execute(
        """
        UPDATE users
        SET password_hash = %s,
            auth_version = auth_version + 1,
            failed_login_count = 0,
            last_failed_login_at = NULL,
            locked_until = NULL,
            updated_at = NOW()
        WHERE id = %s
        """,
        (password_hash, user.id),
    )
    log_audit("admin_password_reset", f"Password reset for {user.email}")
    flash(f"Password updated for {user.display_name}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.from_row(fetch_one("SELECT * FROM users WHERE id = %s", (user_id,)))
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.users"))
    if user.is_admin and is_last_active_admin(user.id):
        flash("Keep at least one active administrator account.", "danger")
        return redirect(url_for("admin.users"))

    delete_user_records(user.id)
    log_audit("user_deleted", f"{user.email} was deleted by {current_user.email}")
    flash(f"{user.display_name} was deleted.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * 25
    rows = fetch_all(
        """
        SELECT audit_logs.*, users.email AS user_email
        FROM audit_logs
        LEFT JOIN users ON users.id = audit_logs.user_id
        ORDER BY audit_logs.created_at DESC
        LIMIT 25 OFFSET %s
        """,
        (offset,),
    )
    total_row = fetch_one("SELECT COUNT(*) AS total FROM audit_logs")
    logs = type("Pagination", (), {"items": AuditLog.from_rows(rows), "page": page, "pages": 1, "total": total_row["total"] if total_row else 0, "has_next": False, "has_prev": page > 1})()
    return render_template("admin/audit_logs.html", logs=logs)


def is_last_active_admin(user_id):
    row = fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM users
        WHERE role = 'admin'
          AND is_banned = 0
          AND id <> %s
        """,
        (user_id,),
    )
    return not row or int(row["total"] or 0) == 0


def delete_user_records(user_id):
    """Delete one account and let the frozen foreign-key policy handle dependents."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            cursor.execute(
                """
                DELETE profile_images
                FROM profile_images
                LEFT JOIN users ON users.profile_image = profile_images.image_hash
                WHERE users.id IS NULL
                """
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
