from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from utils.audit import log_audit
from utils.db import execute, fetch_all, fetch_one

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/")
@login_required
def index():
    requests = fetch_all(
        """
        SELECT note_access_requests.*, topics.title AS topic_title,
               COALESCE(users.display_name, 'Deleted administrator') AS admin_name,
               users.email AS admin_email
        FROM note_access_requests
        JOIN topics ON topics.id = note_access_requests.topic_id
        LEFT JOIN users ON users.id = note_access_requests.requester_admin_id
        WHERE topics.owner_id = %s
        ORDER BY note_access_requests.requested_at DESC
        """,
        (current_user.id,),
    )
    notes_by_topic = {
        row["topic_id"]: fetch_all(
            """
            SELECT id, title
            FROM notes
            WHERE owner_id = %s AND topic_id = %s AND is_deleted = 0
            ORDER BY updated_at DESC
            """,
            (current_user.id, row["topic_id"]),
        )
        for row in requests
        if row["status"] == "pending"
    }
    return render_template("notifications/index.html", requests=requests, notes_by_topic=notes_by_topic)


@notifications_bp.route("/<int:request_id>/approve", methods=["POST"])
@login_required
def approve(request_id):
    access_request = get_pending_request_or_404(request_id)
    note_id = request.form.get("note_id", type=int)
    note = fetch_one(
        """
        SELECT id
        FROM notes
        WHERE id = %s AND owner_id = %s AND topic_id = %s AND is_deleted = 0
        """,
        (note_id, current_user.id, access_request["topic_id"]),
    )
    if not note:
        flash("Choose one of your notes for this topic.", "danger")
        return redirect(url_for("notifications.index"))

    execute(
        """
        UPDATE note_access_requests
        SET status = 'approved', note_id = %s, responded_at = NOW()
        WHERE id = %s AND status = 'pending'
        """,
        (note_id, request_id),
    )
    log_audit("note_access_approved", f"Approved note access request {request_id}")
    flash("Note access approved.", "success")
    return redirect(url_for("notifications.index"))


@notifications_bp.route("/<int:request_id>/deny", methods=["POST"])
@login_required
def deny(request_id):
    access_request = get_pending_request_or_404(request_id)
    execute(
        """
        UPDATE note_access_requests
        SET status = 'denied', responded_at = NOW()
        WHERE id = %s AND status = 'pending'
        """,
        (access_request["id"],),
    )
    log_audit("note_access_denied", f"Denied note access request {request_id}")
    flash("Note access denied.", "info")
    return redirect(url_for("notifications.index"))


def get_pending_request_or_404(request_id):
    access_request = fetch_one(
        """
        SELECT note_access_requests.*
        FROM note_access_requests
        JOIN topics ON topics.id = note_access_requests.topic_id
        WHERE note_access_requests.id = %s
          AND topics.owner_id = %s
          AND note_access_requests.status = 'pending'
        """,
        (request_id, current_user.id),
    )
    if not access_request:
        abort(404)
    return access_request
