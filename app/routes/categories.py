from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.models import db
from app.models.category import Category
from utils.helpers import clean_text

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


def get_category_or_404(category_id):
    category = Category.query.filter_by(
        id=category_id,
        owner_id=current_user.id,
        is_deleted=False,
    ).first()
    if not category:
        abort(404)
    return category


@categories_bp.route("/")
@login_required
def index():
    categories = Category.query.filter_by(
        owner_id=current_user.id,
        is_deleted=False,
    ).order_by(Category.name.asc()).all()
    return render_template("categories/index.html", categories=categories)


@categories_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        category = Category(
            name=clean_text(request.form.get("name")),
            description=clean_text(request.form.get("description")),
            color=clean_text(request.form.get("color")) or "#2563eb",
            owner_id=current_user.id,
        )
        if not category.name:
            flash("Category name is required.", "danger")
            return render_template("categories/form.html", category=category)

        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("You already have a category with that name.", "danger")
            return render_template("categories/form.html", category=category)

        flash("Category created successfully.", "success")
        return redirect(url_for("categories.index"))

    return render_template("categories/form.html", category=None)


@categories_bp.route("/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def edit(category_id):
    category = get_category_or_404(category_id)
    if request.method == "POST":
        category.name = clean_text(request.form.get("name"))
        category.description = clean_text(request.form.get("description"))
        category.color = clean_text(request.form.get("color")) or "#2563eb"

        if not category.name:
            flash("Category name is required.", "danger")
            return render_template("categories/form.html", category=category)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("You already have a category with that name.", "danger")
            return render_template("categories/form.html", category=category)

        flash("Category updated successfully.", "success")
        return redirect(url_for("categories.index"))

    return render_template("categories/form.html", category=category)


@categories_bp.route("/<int:category_id>/delete", methods=["POST"])
@login_required
def delete(category_id):
    category = get_category_or_404(category_id)
    category.is_deleted = True
    db.session.commit()
    flash("Category deleted successfully.", "info")
    return redirect(url_for("categories.index"))
