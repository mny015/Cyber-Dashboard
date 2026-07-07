from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.category import Category
from app.models.topic import Topic
from utils.audit import log_audit
from utils.db import execute, fetch_all, fetch_one, fetch_scalar
from utils.helpers import clean_text, slugify

topics_bp = Blueprint("topics", __name__, url_prefix="/topics")


def get_topic_or_404(topic_id):
    topic = Topic.from_row(
        fetch_one(
            "SELECT * FROM topics WHERE id = %s AND owner_id = %s AND is_deleted = 0",
            (topic_id, current_user.id),
        )
    )
    if not topic:
        abort(404)
    return topic


def get_categories():
    return [
        Category.from_row(row)
        for row in fetch_all(
            "SELECT * FROM categories WHERE owner_id = %s AND is_deleted = 0 ORDER BY name ASC",
            (current_user.id,),
        )
    ]


@topics_bp.route("/")
@login_required
def index():
    category_id = request.args.get("category_id", type=int)
    if category_id:
        rows = fetch_all(
            """
            SELECT topics.*, categories.name AS category_name
            FROM topics
            LEFT JOIN categories ON categories.id = topics.category_id
            WHERE topics.owner_id = %s AND topics.is_deleted = 0 AND topics.category_id = %s
            ORDER BY topics.updated_at DESC
            """,
            (current_user.id, category_id),
        )
    else:
        rows = fetch_all(
            """
            SELECT topics.*, categories.name AS category_name
            FROM topics
            LEFT JOIN categories ON categories.id = topics.category_id
            WHERE topics.owner_id = %s AND topics.is_deleted = 0
            ORDER BY topics.updated_at DESC
            """,
            (current_user.id,),
        )
    topics = [Topic.from_row(row) for row in rows]
    return render_template(
        "topics/index.html",
        topics=topics,
        categories=get_categories(),
        selected_category_id=category_id,
    )


@topics_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        topic = Topic(owner_id=current_user.id)
        apply_topic_form(topic)
        if not topic.title:
            flash("Topic title is required.", "danger")
            return render_template("topics/form.html", topic=topic, categories=get_categories())

        if not commit_topic():
            return render_template("topics/form.html", topic=topic, categories=get_categories())

        log_audit("topic_created", f"Created topic {topic.title}")
        flash("Topic created successfully.", "success")
        return redirect(url_for("topics.detail", topic_id=request._topic_id))

    return render_template("topics/form.html", topic=None, categories=get_categories())


@topics_bp.route("/<int:topic_id>")
@login_required
def detail(topic_id):
    topic = get_topic_or_404(topic_id)
    return render_template("topics/detail.html", topic=topic)


@topics_bp.route("/<int:topic_id>/edit", methods=["GET", "POST"])
@login_required
def edit(topic_id):
    topic = get_topic_or_404(topic_id)
    if request.method == "POST":
        request._topic_id = topic.id
        apply_topic_form(topic)
        if not topic.title:
            flash("Topic title is required.", "danger")
            return render_template("topics/form.html", topic=topic, categories=get_categories())

        if not commit_topic():
            return render_template("topics/form.html", topic=topic, categories=get_categories())

        log_audit("topic_updated", f"Updated topic {topic.title}")
        flash("Topic updated successfully.", "success")
        return redirect(url_for("topics.detail", topic_id=topic.id))

    return render_template("topics/form.html", topic=topic, categories=get_categories())


@topics_bp.route("/<int:topic_id>/delete", methods=["POST"])
@login_required
def delete(topic_id):
    topic = get_topic_or_404(topic_id)
    execute(
        "UPDATE topics SET is_deleted = 1, updated_at = NOW() WHERE id = %s AND owner_id = %s",
        (topic.id, current_user.id),
    )
    log_audit("topic_deleted", f"Deleted topic {topic.title}")
    flash("Topic deleted successfully.", "info")
    return redirect(url_for("topics.index"))


def apply_topic_form(topic):
    topic.title = clean_text(request.form.get("title"))
    topic.slug = slugify(topic.title)
    topic.description = clean_text(request.form.get("description"))
    topic.status = clean_text(request.form.get("status")) or "planned"
    topic.priority = clean_text(request.form.get("priority")) or "medium"
    topic.notes = clean_text(request.form.get("notes"))
    topic.category_id = request.form.get("category_id", type=int) or None


def commit_topic():
    try:
        topic_id = getattr(request, "_topic_id", None)
        duplicate_count = fetch_scalar(
            """
            SELECT COUNT(*)
            FROM topics
            WHERE owner_id = %s AND slug = %s AND is_deleted = 0
              AND (%s IS NULL OR id <> %s)
            """,
            (current_user.id, slugify(clean_text(request.form.get("title"))), topic_id, topic_id),
            default=0,
        )
        if duplicate_count:
            raise ValueError("duplicate")
        if topic_id:
            execute(
                """
                UPDATE topics
                SET title = %s, slug = %s, description = %s, status = %s, priority = %s, notes = %s,
                    category_id = %s, updated_at = NOW()
                WHERE id = %s AND owner_id = %s AND is_deleted = 0
                """,
                (
                    clean_text(request.form.get("title")),
                    slugify(clean_text(request.form.get("title"))),
                    clean_text(request.form.get("description")),
                    clean_text(request.form.get("status")) or "planned",
                    clean_text(request.form.get("priority")) or "medium",
                    clean_text(request.form.get("notes")),
                    request.form.get("category_id", type=int) or None,
                    topic_id,
                    current_user.id,
                ),
            )
        else:
            _, new_id = execute(
                """
                INSERT INTO topics (title, slug, description, status, priority, notes, is_deleted, category_id, owner_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s, NOW(), NOW())
                """,
                (
                    clean_text(request.form.get("title")),
                    slugify(clean_text(request.form.get("title"))),
                    clean_text(request.form.get("description")),
                    clean_text(request.form.get("status")) or "planned",
                    clean_text(request.form.get("priority")) or "medium",
                    clean_text(request.form.get("notes")),
                    request.form.get("category_id", type=int) or None,
                    current_user.id,
                ),
            )
            request._topic_id = new_id
        return True
    except Exception:
        flash("You already have a topic with that title.", "danger")
        return False
