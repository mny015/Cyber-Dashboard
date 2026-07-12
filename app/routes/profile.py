"""Profile URL mappings."""

from flask import Blueprint

from app.controllers import profile_controller


profile_bp = Blueprint("profile", __name__, url_prefix="/profile")
profile_bp.add_url_rule(
    "/", endpoint="edit", view_func=profile_controller.edit, methods=["GET", "POST"]
)
profile_bp.add_url_rule(
    "/picture/<image_hash>",
    endpoint="picture",
    view_func=profile_controller.picture,
    methods=["GET"],
)
