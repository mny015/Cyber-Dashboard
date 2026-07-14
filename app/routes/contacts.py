"""Contact URL mappings."""

from flask import Blueprint

from app.controllers import contacts_controller

contacts_bp = Blueprint("contacts", __name__, url_prefix="/contacts")
contacts_bp.add_url_rule("/", endpoint="index", view_func=contacts_controller.index, methods=["GET"])
contacts_bp.add_url_rule(
    "/new", endpoint="create", view_func=contacts_controller.create, methods=["GET", "POST"]
)
contacts_bp.add_url_rule(
    "/<int:contact_id>/edit",
    endpoint="edit",
    view_func=contacts_controller.edit,
    methods=["GET", "POST"],
)
contacts_bp.add_url_rule(
    "/<int:contact_id>/delete",
    endpoint="delete",
    view_func=contacts_controller.delete,
    methods=["POST"],
)
