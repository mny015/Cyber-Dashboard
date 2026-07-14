"""Security finding and catalog URL mappings."""

from flask import Blueprint

from app.controllers import security_controller

security_bp = Blueprint("security", __name__, url_prefix="/security")
security_bp.add_url_rule("/", endpoint="index", view_func=security_controller.index, methods=["GET"])
security_bp.add_url_rule(
    "/new", endpoint="create", view_func=security_controller.create, methods=["GET", "POST"]
)
security_bp.add_url_rule(
    "/<int:finding_id>/edit",
    endpoint="edit",
    view_func=security_controller.edit,
    methods=["GET", "POST"],
)
security_bp.add_url_rule(
    "/<int:finding_id>/delete",
    endpoint="delete",
    view_func=security_controller.delete,
    methods=["POST"],
)
security_bp.add_url_rule(
    "/vulnerabilities/suggest",
    endpoint="suggest_vulnerability",
    view_func=security_controller.suggest_vulnerability,
    methods=["POST"],
)
security_bp.add_url_rule(
    "/admin/vulnerabilities",
    endpoint="admin_vulnerabilities",
    view_func=security_controller.admin_vulnerabilities,
    methods=["GET", "POST"],
)
security_bp.add_url_rule(
    "/admin/vulnerabilities/<int:vulnerability_id>/approve",
    endpoint="approve_vulnerability",
    view_func=security_controller.approve_vulnerability,
    methods=["POST"],
)
security_bp.add_url_rule(
    "/admin/vulnerabilities/<int:vulnerability_id>/reject",
    endpoint="reject_vulnerability",
    view_func=security_controller.reject_vulnerability,
    methods=["POST"],
)
