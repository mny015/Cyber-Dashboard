"""HTTP handlers for note-access notifications."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import flash_form_errors, validate_action
from app.forms.notifications import NoteApprovalForm
from app.repositories import notification_repository
from app.services import notification_service
from app.services.exceptions import NotFoundError, PermissionDeniedError
from app.utils.audit import get_audit_context
from app.utils.decorators import recent_reauthentication_required


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
    approval_forms = {}
    for row in requests:
        if row.status != "pending":
            continue
        form = NoteApprovalForm()
        form.note_id.choices = [
            (note.id, note.title) for note in notes_by_topic.get(row.topic_id, [])
        ]
        approval_forms[row.id] = form
    return render_template(
        "notifications/index.html",
        requests=requests,
        notes_by_topic=notes_by_topic,
        approval_forms=approval_forms,
    )


@login_required
@recent_reauthentication_required
def approve(request_id):
    access_request = _get_pending_request_or_404(request_id)
    form = NoteApprovalForm()
    form.note_id.choices = [
        (note.id, note.title)
        for note in notification_repository.list_notes_for_topic(
            current_user.id, access_request.topic_id
        )
    ]
    if not form.validate_on_submit():
        flash_form_errors(form, "Choose one of your notes for this topic.")
        return redirect(url_for("notifications.index"))
    try:
        notification_service.approve_request(
            request_id, current_user.id, form.note_id.data, get_audit_context()
        )
    except PermissionDeniedError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("notifications.index"))
    flash("Note access approved.", "success")
    return redirect(url_for("notifications.index"))


@login_required
def deny(request_id):
    if not validate_action():
        return redirect(url_for("notifications.index"))
    _get_pending_request_or_404(request_id)
    try:
        notification_service.deny_request(
            request_id, current_user.id, get_audit_context()
        )
    except NotFoundError:
        abort(404)
    flash("Note access denied.", "info")
    return redirect(url_for("notifications.index"))
