"""HTTP handlers for user-owned learning topics."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.topic import Topic
from app.repositories import category_repository, topic_repository
from app.utils.database import DatabaseIntegrityError
from utils.audit import log_audit
from utils.helpers import clean_text, slugify


def _get_topic_or_404(topic_id):
    topic = topic_repository.find_owned(topic_id, current_user.id)
    if not topic:
        abort(404)
    return topic


def _categories():
    return category_repository.list_for_user(current_user.id)


@login_required
def index():
    category_id = request.args.get("category_id", type=int)
    return render_template(
        "topics/index.html",
        topics=topic_repository.list_for_user(current_user.id, category_id=category_id),
        categories=_categories(),
        selected_category_id=category_id,
    )


@login_required
def create():
    if request.method != "POST":
        return render_template("topics/form.html", topic=None, categories=_categories())

    topic = Topic(owner_id=current_user.id)
    _apply_form(topic)
    if not topic.title:
        flash("Topic title is required.", "danger")
        return render_template("topics/form.html", topic=topic, categories=_categories())
    if not _save(topic):
        return render_template("topics/form.html", topic=topic, categories=_categories())

    log_audit("topic_created", f"Created topic {topic.title}")
    flash("Topic created successfully.", "success")
    return redirect(url_for("topics.detail", topic_id=topic.id))


@login_required
def detail(topic_id):
    return render_template("topics/detail.html", topic=_get_topic_or_404(topic_id))


@login_required
def edit(topic_id):
    topic = _get_topic_or_404(topic_id)
    if request.method != "POST":
        return render_template("topics/form.html", topic=topic, categories=_categories())

    _apply_form(topic)
    if not topic.title:
        flash("Topic title is required.", "danger")
        return render_template("topics/form.html", topic=topic, categories=_categories())
    if not _save(topic):
        return render_template("topics/form.html", topic=topic, categories=_categories())

    log_audit("topic_updated", f"Updated topic {topic.title}")
    flash("Topic updated successfully.", "success")
    return redirect(url_for("topics.detail", topic_id=topic.id))


@login_required
def delete(topic_id):
    topic = _get_topic_or_404(topic_id)
    topic_repository.delete_owned(topic.id, current_user.id)
    log_audit("topic_deleted", f"Deleted topic {topic.title}")
    flash("Topic deleted successfully.", "info")
    return redirect(url_for("topics.index"))


def _apply_form(topic):
    topic.title = clean_text(request.form.get("title"))
    topic.slug = slugify(topic.title)
    topic.description = clean_text(request.form.get("description"))
    topic.status = clean_text(request.form.get("status")) or "planned"
    topic.priority = clean_text(request.form.get("priority")) or "medium"
    topic.notes = clean_text(request.form.get("notes"))
    topic.category_id = request.form.get("category_id", type=int) or None


def _save(topic):
    if topic_repository.slug_exists(
        current_user.id, topic.slug, exclude_topic_id=topic.id
    ):
        flash("You already have a topic with that title.", "danger")
        return False
    try:
        if topic.id:
            topic_repository.update_owned(topic, current_user.id)
        else:
            topic_repository.create(topic)
    except DatabaseIntegrityError:
        flash("You already have a topic with that title.", "danger")
        return False
    return True
