from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.category import Category
from utils.db import execute, fetch_all, fetch_one
from utils.helpers import clean_text

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


def get_category_or_404(category_id):
    category = Category.from_row(
        fetch_one(
            "SELECT * FROM categories WHERE id = %s AND owner_id = %s AND is_deleted = 0",
            (category_id, current_user.id),
        )
    )
    if not category:
        abort(404)
    return category


@categories_bp.route("/")
@login_required
def index():
    categories = [
        Category.from_row(row)
        for row in fetch_all(
            "SELECT * FROM categories WHERE owner_id = %s AND is_deleted = 0 ORDER BY name ASC",
            (current_user.id,),
        )
    ]
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

        try:
            _, category.id = execute(
                """
                INSERT INTO categories (name, description, color, is_deleted, owner_id, created_at, updated_at)
                VALUES (%s, %s, %s, 0, %s, NOW(), NOW())
                """,
                (category.name, category.description, category.color, category.owner_id),
            )
        except Exception:
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
            execute(
                """
                UPDATE categories
                SET name = %s, description = %s, color = %s, updated_at = NOW()
                WHERE id = %s AND owner_id = %s AND is_deleted = 0
                """,
                (category.name, category.description, category.color, category.id, current_user.id),
            )
        except Exception:
            flash("You already have a category with that name.", "danger")
            return render_template("categories/form.html", category=category)

        flash("Category updated successfully.", "success")
        return redirect(url_for("categories.index"))

    return render_template("categories/form.html", category=category)


@categories_bp.route("/<int:category_id>/delete", methods=["POST"])
@login_required
def delete(category_id):
    category = get_category_or_404(category_id)
    execute(
        "UPDATE categories SET is_deleted = 1, updated_at = NOW() WHERE id = %s AND owner_id = %s",
        (category.id, current_user.id),
    )
    flash("Category deleted successfully.", "info")
    return redirect(url_for("categories.index"))
