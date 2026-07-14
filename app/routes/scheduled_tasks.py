"""Scheduled task URL mappings."""

from flask import Blueprint

from app.controllers import scheduled_tasks_controller

tasks_bp = Blueprint("tasks", __name__, url_prefix="/scheduled-tasks")
tasks_bp.add_url_rule(
    "/", endpoint="index", view_func=scheduled_tasks_controller.index, methods=["GET", "POST"]
)
tasks_bp.add_url_rule(
    "/<int:task_id>/complete",
    endpoint="complete",
    view_func=scheduled_tasks_controller.complete,
    methods=["POST"],
)
tasks_bp.add_url_rule(
    "/<int:task_id>/cancel",
    endpoint="cancel",
    view_func=scheduled_tasks_controller.cancel,
    methods=["POST"],
)
