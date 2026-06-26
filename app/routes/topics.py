from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.models import db
from app.models.category import Category
from app.models.topic import Topic
from utils.helpers import clean_text, slugify

topics_bp = Blueprint("topics", __name__, url_prefix="/topics")


def get_topic_or_404(topic_id):
    topic = Topic.query.filter_by(
        id=topic_id,
        owner_id=current_user.id,
        is_deleted=False,
    ).first()
    if not topic:
        abort(404)
    return topic


def get_categories():
    return Category.query.filter_by(
        owner_id=current_user.id,
        is_deleted=False,
    ).order_by(Category.name.asc()).all()


@topics_bp.route("/")
@login_required
def index():
    category_id = request.args.get("category_id", type=int)
    query = Topic.query.filter_by(owner_id=current_user.id, is_deleted=False)
    if category_id:
        query = query.filter_by(category_id=category_id)
    topics = query.order_by(Topic.updated_at.desc()).all()
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

        db.session.add(topic)
        if not commit_topic():
            return render_template("topics/form.html", topic=topic, categories=get_categories())

        flash("Topic created successfully.", "success")
        return redirect(url_for("topics.detail", topic_id=topic.id))

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
        apply_topic_form(topic)
        if not topic.title:
            flash("Topic title is required.", "danger")
            return render_template("topics/form.html", topic=topic, categories=get_categories())

        if not commit_topic():
            return render_template("topics/form.html", topic=topic, categories=get_categories())

        flash("Topic updated successfully.", "success")
        return redirect(url_for("topics.detail", topic_id=topic.id))

    return render_template("topics/form.html", topic=topic, categories=get_categories())


@topics_bp.route("/<int:topic_id>/delete", methods=["POST"])
@login_required
def delete(topic_id):
    topic = get_topic_or_404(topic_id)
    topic.is_deleted = True
    db.session.commit()
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
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        flash("You already have a topic with that title.", "danger")
        return False
