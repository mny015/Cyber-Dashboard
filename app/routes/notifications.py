"""Notification URL mappings."""

from flask import Blueprint

from app.controllers import notifications_controller

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")
notifications_bp.add_url_rule(
    "/", endpoint="index", view_func=notifications_controller.index, methods=["GET"]
)
notifications_bp.add_url_rule(
    "/<int:request_id>/approve",
    endpoint="approve",
    view_func=notifications_controller.approve,
    methods=["POST"],
)
notifications_bp.add_url_rule(
    "/<int:request_id>/deny",
    endpoint="deny",
    view_func=notifications_controller.deny,
    methods=["POST"],
)
