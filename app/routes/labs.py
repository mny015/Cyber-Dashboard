"""Lab URL mappings."""

from flask import Blueprint

from app.controllers import labs_controller

labs_bp = Blueprint("labs", __name__, url_prefix="/labs")
labs_bp.add_url_rule("/", endpoint="index", view_func=labs_controller.index, methods=["GET"])
labs_bp.add_url_rule(
    "/new", endpoint="create", view_func=labs_controller.create, methods=["GET", "POST"]
)
labs_bp.add_url_rule(
    "/<int:lab_id>", endpoint="detail", view_func=labs_controller.detail, methods=["GET"]
)
labs_bp.add_url_rule(
    "/<int:lab_id>/edit",
    endpoint="edit",
    view_func=labs_controller.edit,
    methods=["GET", "POST"],
)
labs_bp.add_url_rule(
    "/<int:lab_id>/delete", endpoint="delete", view_func=labs_controller.delete, methods=["POST"]
)
labs_bp.add_url_rule(
    "/<int:lab_id>/complete",
    endpoint="complete",
    view_func=labs_controller.complete,
    methods=["POST"],
)
labs_bp.add_url_rule(
    "/<int:lab_id>/incomplete",
    endpoint="incomplete",
    view_func=labs_controller.incomplete,
    methods=["POST"],
)
