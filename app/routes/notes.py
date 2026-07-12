from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import Note
from app.repositories import note_repository, topic_repository
from app.services import note_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from utils.audit import get_audit_context
from utils.helpers import clean_text

notes_bp = Blueprint("notes", __name__, url_prefix="/notes")


def get_note_or_404(note_id):
    note = note_repository.find_owned(note_id, current_user.id)
    if not note:
        abort(404)
    return note


def get_user_topics():
    return topic_repository.list_active(current_user.id)


def get_topics_with_note_counts():
    return note_repository.topic_summaries(current_user.id)


@notes_bp.route("/")
@login_required
def index():
    topic_id = request.args.get("topic_id", type=int)
    query = clean_text(request.args.get("q"))
    if topic_id and not user_owns_topic(topic_id):
        abort(404)

    notes = note_repository.list_for_user(current_user.id, topic_id=topic_id, search=query)
    stats = note_repository.stats_for_user(current_user.id)

    return render_template(
        "notes/index.html",
        notes=notes,
        topics=get_topics_with_note_counts(),
        selected_topic_id=topic_id,
        query=query,
        stats=stats,
    )


@notes_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    topic_id = request.args.get("topic_id", type=int)
    if request.method == "POST":
        title = clean_text(request.form.get("title"))
        body = clean_text(request.form.get("body"))
        topic_id = request.form.get("topic_id", type=int) or None
        try:
            note = note_service.create_note(
                current_user.id, title, body, topic_id, get_audit_context()
            )
        except ValidationError as exc:
            flash(str(exc), "danger")
            return render_template("notes/form.html", note=request.form, topics=get_user_topics())
        except PermissionDeniedError:
            abort(403)
        flash("Note created successfully.", "success")
        return redirect(url_for("notes.detail", note_id=note.id))

    return render_template("notes/form.html", note={"topic_id": topic_id}, topics=get_user_topics())


@notes_bp.route("/<int:note_id>")
@login_required
def detail(note_id):
    return render_template("notes/detail.html", note=get_note_or_404(note_id))


@notes_bp.route("/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit(note_id):
    note = get_note_or_404(note_id)
    if request.method == "POST":
        title = clean_text(request.form.get("title"))
        body = clean_text(request.form.get("body"))
        topic_id = request.form.get("topic_id", type=int) or None
        try:
            note_service.update_note(
                note_id, current_user.id, title, body, topic_id, get_audit_context()
            )
        except ValidationError as exc:
            flash(str(exc), "danger")
            return render_template("notes/form.html", note=request.form, topics=get_user_topics())
        except PermissionDeniedError:
            abort(403)
        except NotFoundError:
            abort(404)
        flash("Note updated successfully.", "success")
        return redirect(url_for("notes.detail", note_id=note_id))

    return render_template("notes/form.html", note=note, topics=get_user_topics())


@notes_bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete(note_id):
    try:
        note_service.delete_note(note_id, current_user.id, get_audit_context())
    except NotFoundError:
        abort(404)
    flash("Note deleted successfully.", "info")
    return redirect(url_for("notes.index"))


def user_owns_topic(topic_id):
    return topic_repository.exists_owned(topic_id, current_user.id)
