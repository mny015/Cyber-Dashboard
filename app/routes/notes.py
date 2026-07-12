from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import Note
from app.repositories import note_repository, topic_repository
from utils.audit import log_audit
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
        if not title or not body:
            flash("Note title and body are required.", "danger")
            return render_template("notes/form.html", note=request.form, topics=get_user_topics())

        if topic_id and not user_owns_topic(topic_id):
            abort(403)

        note = note_repository.create(
            Note(title=title, body=body, topic_id=topic_id, owner_id=current_user.id)
        )
        log_audit("note_created", f"Created note {note.id}")
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
        if not title or not body:
            flash("Note title and body are required.", "danger")
            return render_template("notes/form.html", note=request.form, topics=get_user_topics())

        if topic_id and not user_owns_topic(topic_id):
            abort(403)

        note.title = title
        note.body = body
        note.topic_id = topic_id
        note_repository.update_owned(note, current_user.id)
        log_audit("note_updated", f"Updated note {note_id}")
        flash("Note updated successfully.", "success")
        return redirect(url_for("notes.detail", note_id=note_id))

    return render_template("notes/form.html", note=note, topics=get_user_topics())


@notes_bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete(note_id):
    note = get_note_or_404(note_id)
    note_repository.delete_owned(note.id, current_user.id)
    log_audit("note_deleted", f"Deleted note {note.id}")
    flash("Note deleted successfully.", "info")
    return redirect(url_for("notes.index"))


def user_owns_topic(topic_id):
    return topic_repository.exists_owned(topic_id, current_user.id)
