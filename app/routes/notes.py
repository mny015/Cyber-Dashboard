from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from utils.audit import log_audit
from utils.db import execute, fetch_all, fetch_one
from utils.helpers import clean_text

notes_bp = Blueprint("notes", __name__, url_prefix="/notes")


def get_note_or_404(note_id):
    note = fetch_one(
        """
        SELECT notes.*, topics.title AS topic_title
        FROM notes
        LEFT JOIN topics ON topics.id = notes.topic_id
        WHERE notes.id = %s AND notes.owner_id = %s AND notes.is_deleted = 0
        """,
        (note_id, current_user.id),
    )
    if not note:
        abort(404)
    return note


def get_user_topics():
    return fetch_all(
        """
        SELECT id, title
        FROM topics
        WHERE owner_id = %s AND is_deleted = 0
        ORDER BY title ASC
        """,
        (current_user.id,),
    )


def get_topics_with_note_counts():
    return fetch_all(
        """
        SELECT topics.id, topics.title, COUNT(notes.id) AS note_count
        FROM topics
        LEFT JOIN notes
          ON notes.topic_id = topics.id
         AND notes.owner_id = %s
         AND notes.is_deleted = 0
        WHERE topics.owner_id = %s AND topics.is_deleted = 0
        GROUP BY topics.id, topics.title
        ORDER BY topics.title ASC
        """,
        (current_user.id, current_user.id),
    )


@notes_bp.route("/")
@login_required
def index():
    topic_id = request.args.get("topic_id", type=int)
    query = clean_text(request.args.get("q"))
    if topic_id and not user_owns_topic(topic_id):
        abort(404)

    search_value = f"%{query}%"
    notes = fetch_all(
        """
        SELECT notes.*, topics.title AS topic_title
        FROM notes
        LEFT JOIN topics ON topics.id = notes.topic_id
        WHERE notes.owner_id = %s
          AND notes.is_deleted = 0
          AND (%s IS NULL OR notes.topic_id = %s)
          AND (%s = '' OR notes.title LIKE %s OR notes.body LIKE %s)
        ORDER BY notes.updated_at DESC
        """,
        (current_user.id, topic_id, topic_id, query, search_value, search_value),
    )
    stats = fetch_one(
        """
        SELECT COUNT(*) AS total_notes, MAX(updated_at) AS last_updated
        FROM notes
        WHERE owner_id = %s AND is_deleted = 0
        """,
        (current_user.id,),
    )

    return render_template(
        "notes/index.html",
        notes=notes,
        topics=get_topics_with_note_counts(),
        selected_topic_id=topic_id,
        query=query,
        stats=stats or {"total_notes": 0, "last_updated": None},
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

        _, note_id = execute(
            """
            INSERT INTO notes (title, body, topic_id, owner_id, is_deleted, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 0, NOW(), NOW())
            """,
            (title, body, topic_id, current_user.id),
        )
        log_audit("note_created", f"Created note {note_id}")
        flash("Note created successfully.", "success")
        return redirect(url_for("notes.detail", note_id=note_id))

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

        execute(
            """
            UPDATE notes
            SET title = %s, body = %s, topic_id = %s, updated_at = NOW()
            WHERE id = %s AND owner_id = %s AND is_deleted = 0
            """,
            (title, body, topic_id, note_id, current_user.id),
        )
        log_audit("note_updated", f"Updated note {note_id}")
        flash("Note updated successfully.", "success")
        return redirect(url_for("notes.detail", note_id=note_id))

    return render_template("notes/form.html", note=note, topics=get_user_topics())


@notes_bp.route("/<int:note_id>/delete", methods=["POST"])
@login_required
def delete(note_id):
    note = get_note_or_404(note_id)
    execute(
        "UPDATE notes SET is_deleted = 1, updated_at = NOW() WHERE id = %s AND owner_id = %s",
        (note["id"], current_user.id),
    )
    log_audit("note_deleted", f"Deleted note {note['id']}")
    flash("Note deleted successfully.", "info")
    return redirect(url_for("notes.index"))


def user_owns_topic(topic_id):
    return bool(
        fetch_one(
            "SELECT id FROM topics WHERE id = %s AND owner_id = %s AND is_deleted = 0",
            (topic_id, current_user.id),
        )
    )
