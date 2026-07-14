"""Topic URL mappings."""

from flask import Blueprint

from app.controllers import topics_controller

topics_bp = Blueprint("topics", __name__, url_prefix="/topics")
topics_bp.add_url_rule("/", endpoint="index", view_func=topics_controller.index, methods=["GET"])
topics_bp.add_url_rule(
    "/new", endpoint="create", view_func=topics_controller.create, methods=["GET", "POST"]
)
topics_bp.add_url_rule(
    "/<int:topic_id>", endpoint="detail", view_func=topics_controller.detail, methods=["GET"]
)
topics_bp.add_url_rule(
    "/<int:topic_id>/edit",
    endpoint="edit",
    view_func=topics_controller.edit,
    methods=["GET", "POST"],
)
topics_bp.add_url_rule(
    "/<int:topic_id>/delete",
    endpoint="delete",
    view_func=topics_controller.delete,
    methods=["POST"],
)
