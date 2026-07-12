from flask import Blueprint, render_template, send_file
from flask_login import current_user, login_required

from app.services import export_service
from utils.audit import get_audit_context
from utils.decorators import admin_required
from utils.export_utils import csv_zip_bytes, export_filename, json_bytes

backup_bp = Blueprint("backup", __name__, url_prefix="/backup")


@backup_bp.route("/")
@login_required
def index():
    return render_template("backup/index.html")


@backup_bp.route("/personal.json")
@login_required
def personal_json():
    data = export_service.personal_export(current_user.id, "json", get_audit_context())
    return send_file(
        json_bytes(data),
        mimetype="application/json",
        as_attachment=True,
        download_name=export_filename("personal", "json"),
    )


@backup_bp.route("/personal.zip")
@login_required
def personal_csv():
    data = export_service.personal_export(current_user.id, "zip", get_audit_context())
    return send_file(
        csv_zip_bytes(data),
        mimetype="application/zip",
        as_attachment=True,
        download_name=export_filename("personal", "zip"),
    )


@backup_bp.route("/admin.json")
@login_required
@admin_required
def admin_json():
    data = export_service.admin_export(current_user.id, "json", get_audit_context())
    return send_file(
        json_bytes(data),
        mimetype="application/json",
        as_attachment=True,
        download_name=export_filename("admin", "json"),
    )


@backup_bp.route("/admin.zip")
@login_required
@admin_required
def admin_csv():
    data = export_service.admin_export(current_user.id, "zip", get_audit_context())
    return send_file(
        csv_zip_bytes(data),
        mimetype="application/zip",
        as_attachment=True,
        download_name=export_filename("admin", "zip"),
    )
