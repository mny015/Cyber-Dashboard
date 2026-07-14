"""Category URL mappings."""

from flask import Blueprint

from app.controllers import categories_controller

categories_bp = Blueprint("categories", __name__, url_prefix="/categories")
categories_bp.add_url_rule(
    "/", endpoint="index", view_func=categories_controller.index, methods=["GET"]
)
categories_bp.add_url_rule(
    "/new", endpoint="create", view_func=categories_controller.create, methods=["GET", "POST"]
)
categories_bp.add_url_rule(
    "/<int:category_id>/edit",
    endpoint="edit",
    view_func=categories_controller.edit,
    methods=["GET", "POST"],
)
categories_bp.add_url_rule(
    "/<int:category_id>/delete",
    endpoint="delete",
    view_func=categories_controller.delete,
    methods=["POST"],
)
