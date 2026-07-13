"""HTTP handlers for user-owned learning topics."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import validate_action
from app.forms.topics import TopicForm
from app.models.topic import Topic
from app.repositories import category_repository, topic_repository
from app.utils.database import DatabaseIntegrityError
from utils.audit import log_audit
from utils.helpers import slugify


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
    categories = _categories()
    form = _topic_form(categories)
    if not form.validate_on_submit():
        return render_template(
            "topics/form.html", topic=None, categories=categories, form=form
        )
    topic = Topic(owner_id=current_user.id)
    _apply_form(topic, form)
    if not _save(topic):
        return render_template(
            "topics/form.html", topic=topic, categories=categories, form=form
        )

    log_audit("topic_created", f"Created topic {topic.title}")
    flash("Topic created successfully.", "success")
    return redirect(url_for("topics.detail", topic_id=topic.id))


@login_required
def detail(topic_id):
    return render_template("topics/detail.html", topic=_get_topic_or_404(topic_id))


@login_required
def edit(topic_id):
    topic = _get_topic_or_404(topic_id)
    categories = _categories()
    form = _topic_form(categories, topic)
    if not form.validate_on_submit():
        return render_template(
            "topics/form.html", topic=topic, categories=categories, form=form
        )

    _apply_form(topic, form)
    if not _save(topic):
        return render_template(
            "topics/form.html", topic=topic, categories=categories, form=form
        )

    log_audit("topic_updated", f"Updated topic {topic.title}")
    flash("Topic updated successfully.", "success")
    return redirect(url_for("topics.detail", topic_id=topic.id))


@login_required
def delete(topic_id):
    if not validate_action():
        return redirect(url_for("topics.index"))
    topic = _get_topic_or_404(topic_id)
    topic_repository.delete_owned(topic.id, current_user.id)
    log_audit("topic_deleted", f"Deleted topic {topic.title}")
    flash("Topic deleted successfully.", "info")
    return redirect(url_for("topics.index"))


def _topic_form(categories, topic=None):
    form = TopicForm(obj=topic)
    form.category_id.choices = [(None, "No category")] + [
        (category.id, category.name) for category in categories
    ]
    return form


def _apply_form(topic, form):
    topic.title = form.title.data
    topic.slug = slugify(topic.title)
    topic.description = form.description.data or ""
    topic.status = form.status.data
    topic.priority = form.priority.data
    topic.notes = form.notes.data or ""
    topic.category_id = form.category_id.data


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
