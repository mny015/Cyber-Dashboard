"""HTTP handlers for the user note editor."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import validate_action
from app.forms.notes import NoteForm
from app.repositories import note_repository, topic_repository
from app.services import note_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.utils.audit import get_audit_context
from app.utils.decorators import require_owned_record
from app.utils.validation import clean_text


def _get_note_or_404(note_id):
    return require_owned_record(note_repository.find_owned(note_id, current_user.id))


def _topics():
    return topic_repository.list_active(current_user.id)


@login_required
def index():
    topic_id = request.args.get("topic_id", type=int)
    query = clean_text(request.args.get("q"))
    if topic_id and not topic_repository.exists_owned(topic_id, current_user.id):
        abort(404)
    return render_template(
        "notes/index.html",
        notes=note_repository.list_for_user(current_user.id, topic_id=topic_id, search=query),
        topics=note_repository.topic_summaries(current_user.id),
        selected_topic_id=topic_id,
        query=query,
        stats=note_repository.stats_for_user(current_user.id),
    )


@login_required
def create():
    topic_id = request.args.get("topic_id", type=int)
    topics = _topics()
    form = _note_form(topics)
    if request.method == "GET" and topic_id is not None:
        form.topic_id.data = topic_id
    if not form.validate_on_submit():
        return render_template("notes/form.html", note=None, topics=topics, form=form)
    try:
        note = note_service.create_note(
            current_user.id,
            form.title.data,
            form.body.data,
            form.topic_id.data,
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return render_template("notes/form.html", note=None, topics=topics, form=form)
    except PermissionDeniedError:
        abort(403)
    flash("Note created successfully.", "success")
    return redirect(url_for("notes.detail", note_id=note.id))


@login_required
def detail(note_id):
    return render_template("notes/detail.html", note=_get_note_or_404(note_id))


@login_required
def edit(note_id):
    note = _get_note_or_404(note_id)
    topics = _topics()
    form = _note_form(topics, note)
    if not form.validate_on_submit():
        return render_template("notes/form.html", note=note, topics=topics, form=form)
    try:
        note_service.update_note(
            note_id,
            current_user.id,
            form.title.data,
            form.body.data,
            form.topic_id.data,
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return render_template("notes/form.html", note=note, topics=topics, form=form)
    except PermissionDeniedError:
        abort(403)
    except NotFoundError:
        abort(404)
    flash("Note updated successfully.", "success")
    return redirect(url_for("notes.detail", note_id=note_id))


@login_required
def delete(note_id):
    if not validate_action():
        return redirect(url_for("notes.index"))
    try:
        note_service.delete_note(note_id, current_user.id, get_audit_context())
    except NotFoundError:
        abort(404)
    flash("Note deleted successfully.", "info")
    return redirect(url_for("notes.index"))


def _note_form(topics, note=None):
    form = NoteForm(obj=note)
    form.topic_id.choices = [(None, "No topic")] + [
        (topic.id, topic.title) for topic in topics
    ]
    return form
