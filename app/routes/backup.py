"""Backup and export URL mappings."""

from flask import Blueprint

from app.controllers import backup_controller


backup_bp = Blueprint("backup", __name__, url_prefix="/backup")
backup_bp.add_url_rule("/", endpoint="index", view_func=backup_controller.index, methods=["GET"])
backup_bp.add_url_rule(
    "/personal.json", endpoint="personal_json", view_func=backup_controller.personal_json, methods=["POST"]
)
backup_bp.add_url_rule(
    "/personal.zip", endpoint="personal_csv", view_func=backup_controller.personal_csv, methods=["POST"]
)
backup_bp.add_url_rule(
    "/admin.json", endpoint="admin_json", view_func=backup_controller.admin_json, methods=["POST"]
)
backup_bp.add_url_rule(
    "/admin.zip", endpoint="admin_csv", view_func=backup_controller.admin_csv, methods=["POST"]
)
backup_bp.add_url_rule(
    "/download/<token>", endpoint="download", view_func=backup_controller.download, methods=["GET"]
)
