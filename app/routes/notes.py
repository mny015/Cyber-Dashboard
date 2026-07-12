"""Note URL mappings."""

from flask import Blueprint

from app.controllers import notes_controller


notes_bp = Blueprint("notes", __name__, url_prefix="/notes")
notes_bp.add_url_rule("/", endpoint="index", view_func=notes_controller.index, methods=["GET"])
notes_bp.add_url_rule(
    "/new", endpoint="create", view_func=notes_controller.create, methods=["GET", "POST"]
)
notes_bp.add_url_rule(
    "/<int:note_id>", endpoint="detail", view_func=notes_controller.detail, methods=["GET"]
)
notes_bp.add_url_rule(
    "/<int:note_id>/edit",
    endpoint="edit",
    view_func=notes_controller.edit,
    methods=["GET", "POST"],
)
notes_bp.add_url_rule(
    "/<int:note_id>/delete",
    endpoint="delete",
    view_func=notes_controller.delete,
    methods=["POST"],
)
