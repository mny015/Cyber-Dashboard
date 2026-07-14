"""HTTP handlers for personal and administrator exports."""

import hmac
import secrets
import time

from flask import abort, redirect, render_template, send_file, session, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import validate_action
from app.forms.common import ActionForm
from app.services import export_service
from app.utils.audit import get_audit_context
from app.utils.decorators import admin_required, recent_reauthentication_required
from app.utils.rate_limits import sensitive_action_rate_limited
from utils.export_utils import csv_zip_bytes, export_filename, json_bytes


@login_required
def index():
    return render_template("backup/index.html", action_form=ActionForm())


@login_required
@recent_reauthentication_required
@sensitive_action_rate_limited
def personal_json():
    return _start_export("personal", "json")


@login_required
@recent_reauthentication_required
@sensitive_action_rate_limited
def personal_csv():
    return _start_export("personal", "zip")


@login_required
@admin_required
@recent_reauthentication_required
@sensitive_action_rate_limited
def admin_json():
    return _start_export("admin", "json")


@login_required
@admin_required
@recent_reauthentication_required
@sensitive_action_rate_limited
def admin_csv():
    return _start_export("admin", "zip")


@login_required
def download(token):
    ticket = session.get("export_ticket")
    if not _valid_ticket(ticket, token):
        abort(404)

    scope = ticket["scope"]
    export_format = ticket["format"]
    if scope == "admin" and not current_user.is_admin:
        abort(403)

    data = (
        export_service.admin_data(current_user.id)
        if scope == "admin"
        else export_service.personal_data(current_user.id)
    )
    if export_format == "json":
        return send_file(
            json_bytes(data),
            mimetype="application/json",
            as_attachment=True,
            download_name=export_filename(scope, "json"),
        )
    return send_file(
        csv_zip_bytes(data),
        mimetype="application/zip",
        as_attachment=True,
        download_name=export_filename(scope, "zip"),
    )


def _start_export(scope, export_format):
    if not validate_action():
        return redirect(url_for("backup.index"))
    if scope == "admin":
        export_service.record_admin_export(export_format, get_audit_context())
    else:
        export_service.record_personal_export(export_format, get_audit_context())

    token = secrets.token_urlsafe(24)
    session["export_ticket"] = {
        "token": token,
        "scope": scope,
        "format": export_format,
        "user_id": current_user.id,
        "expires_at": int(time.time()) + 120,
    }
    return redirect(url_for("backup.download", token=token))


def _valid_ticket(ticket, token):
    if not isinstance(ticket, dict):
        return False
    if ticket.get("scope") not in {"personal", "admin"}:
        return False
    if ticket.get("format") not in {"json", "zip"}:
        return False
    if ticket.get("user_id") != current_user.id:
        return False
    if int(ticket.get("expires_at") or 0) < int(time.time()):
        return False
    stored_token = str(ticket.get("token") or "")
    return bool(stored_token) and hmac.compare_digest(stored_token, token)
