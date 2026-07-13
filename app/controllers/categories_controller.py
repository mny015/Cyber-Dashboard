"""HTTP handlers for user-owned categories."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import validate_action
from app.forms.categories import CategoryForm
from app.models.category import Category
from app.repositories import category_repository
from app.utils.database import DatabaseIntegrityError
from utils.audit import log_audit


def _get_category_or_404(category_id):
    category = category_repository.find_owned(category_id, current_user.id)
    if not category:
        abort(404)
    return category


@login_required
def index():
    return render_template(
        "categories/index.html",
        categories=category_repository.list_for_user(current_user.id),
    )


@login_required
def create():
    form = CategoryForm()
    if not form.validate_on_submit():
        return render_template("categories/form.html", category=None, form=form)
    category = Category(
        name=form.name.data,
        description=form.description.data or "",
        color=form.color.data,
        owner_id=current_user.id,
    )
    try:
        category_repository.create(category)
    except DatabaseIntegrityError:
        flash("You already have a category with that name.", "danger")
        return render_template("categories/form.html", category=category, form=form)

    log_audit("category_created", f"Created category {category.name}")
    flash("Category created successfully.", "success")
    return redirect(url_for("categories.index"))


@login_required
def edit(category_id):
    category = _get_category_or_404(category_id)
    form = CategoryForm(obj=category)
    if not form.validate_on_submit():
        return render_template("categories/form.html", category=category, form=form)

    category.name = form.name.data
    category.description = form.description.data or ""
    category.color = form.color.data

    try:
        category_repository.update_owned(category, current_user.id)
    except DatabaseIntegrityError:
        flash("You already have a category with that name.", "danger")
        return render_template("categories/form.html", category=category, form=form)

    log_audit("category_updated", f"Updated category {category.name}")
    flash("Category updated successfully.", "success")
    return redirect(url_for("categories.index"))


@login_required
def delete(category_id):
    if not validate_action():
        return redirect(url_for("categories.index"))
    category = _get_category_or_404(category_id)
    category_repository.delete_owned(category.id, current_user.id)
    log_audit("category_deleted", f"Deleted category {category.name}")
    flash("Category deleted successfully.", "info")
    return redirect(url_for("categories.index"))
