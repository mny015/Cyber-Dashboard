"""HTTP handlers for note-access notifications."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.repositories import notification_repository
from app.services import notification_service
from app.services.exceptions import NotFoundError, PermissionDeniedError
from utils.audit import get_audit_context


def _get_pending_request_or_404(request_id):
    access_request = notification_repository.find_pending_owned(request_id, current_user.id)
    if not access_request:
        abort(404)
    return access_request


@login_required
def index():
    requests = notification_repository.list_for_owner(current_user.id)
    notes_by_topic = {
        row.topic_id: notification_repository.list_notes_for_topic(
            current_user.id, row.topic_id
        )
        for row in requests
        if row.status == "pending"
    }
    return render_template(
        "notifications/index.html", requests=requests, notes_by_topic=notes_by_topic
    )


@login_required
def approve(request_id):
    _get_pending_request_or_404(request_id)
    note_id = request.form.get("note_id", type=int)
    try:
        if not note_id:
            raise PermissionDeniedError("Choose one of your notes for this topic.")
        notification_service.approve_request(
            request_id, current_user.id, note_id, get_audit_context()
        )
    except PermissionDeniedError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("notifications.index"))
    flash("Note access approved.", "success")
    return redirect(url_for("notifications.index"))


@login_required
def deny(request_id):
    _get_pending_request_or_404(request_id)
    try:
        notification_service.deny_request(
            request_id, current_user.id, get_audit_context()
        )
    except NotFoundError:
        abort(404)
    flash("Note access denied.", "info")
    return redirect(url_for("notifications.index"))
