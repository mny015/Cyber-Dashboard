"""HTTP handlers for findings and vulnerability catalog review."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.repositories import security_repository
from app.services import security_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from utils.audit import get_audit_context
from utils.decorators import admin_required
from utils.helpers import clean_text
from utils.security_catalog import ACTIVITY_TYPE_CHOICES, FINDING_STATUS_CHOICES, SEVERITY_CHOICES


@login_required
def index():
    return render_template(
        "security/index.html",
        metrics=security_repository.metrics_for_user(current_user.id),
        findings=security_repository.list_for_user(current_user.id),
        pending_suggestions=security_repository.list_pending_for_creator(current_user.id),
    )


@login_required
def create():
    if request.method == "POST":
        return _save_finding()
    return _render_finding_form({})


@login_required
def edit(finding_id):
    finding = _finding_or_404(finding_id)
    if request.method == "POST":
        return _save_finding(finding_id)
    return _render_finding_form(finding)


@login_required
def delete(finding_id):
    try:
        security_service.delete_finding(finding_id, current_user.id, get_audit_context())
    except NotFoundError:
        abort(404)
    flash("Security finding deleted.", "info")
    return redirect(url_for("security.index"))


@login_required
def suggest_vulnerability():
    try:
        security_service.suggest_vulnerability(
            current_user.id,
            clean_text(request.form.get("name")),
            clean_text(request.form.get("category")) or "User submitted",
            clean_text(request.form.get("default_severity")) or "medium",
            clean_text(request.form.get("description")),
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("security.index"))
    flash("Suggestion submitted for admin review.", "success")
    return redirect(url_for("security.index"))


@login_required
@admin_required
def admin_vulnerabilities():
    if request.method != "POST":
        return render_template(
            "security/admin_vulnerabilities.html",
            pending=security_repository.list_pending_vulnerabilities(),
            vulnerabilities=security_repository.list_all_vulnerabilities(),
            severities=SEVERITY_CHOICES,
        )
    try:
        security_service.save_admin_vulnerability(
            current_user.id,
            {
                "code": clean_text(request.form.get("code")).upper(),
                "name": clean_text(request.form.get("name")),
                "category": clean_text(request.form.get("category")) or "Admin catalog",
                "default_severity": clean_text(request.form.get("default_severity")) or "medium",
                "description": clean_text(request.form.get("description")),
            },
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("security.admin_vulnerabilities"))
    flash("Vulnerability catalog entry saved.", "success")
    return redirect(url_for("security.admin_vulnerabilities"))


@login_required
@admin_required
def approve_vulnerability(vulnerability_id):
    return _review_vulnerability(vulnerability_id, "approved")


@login_required
@admin_required
def reject_vulnerability(vulnerability_id):
    return _review_vulnerability(vulnerability_id, "rejected")


def _save_finding(finding_id=None):
    values = {
        "vulnerability_id": request.form.get("vulnerability_id", type=int) or None,
        "threat_id": request.form.get("threat_id", type=int) or None,
        "activity_type": clean_text(request.form.get("activity_type")),
        "title": clean_text(request.form.get("title")),
        "target": clean_text(request.form.get("target")),
        "severity": clean_text(request.form.get("severity")),
        "status": clean_text(request.form.get("status")),
        "evidence": clean_text(request.form.get("evidence")),
        "notes": clean_text(request.form.get("notes")),
    }
    try:
        security_service.save_finding(
            current_user.id, values, get_audit_context(), finding_id=finding_id
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return redirect(request.referrer or url_for("security.create"))
    except PermissionDeniedError:
        abort(403)
    except NotFoundError:
        abort(404)
    flash(
        "Security finding updated." if finding_id else "Security finding created.",
        "success",
    )
    return redirect(url_for("security.index"))


def _finding_or_404(finding_id):
    finding = security_repository.find_owned(finding_id, current_user.id)
    if not finding:
        abort(404)
    return finding


def _render_finding_form(finding):
    return render_template(
        "security/form.html",
        finding=finding,
        vulnerabilities=security_repository.list_approved_vulnerabilities(),
        threats=security_repository.list_active_threats(),
        activity_types=ACTIVITY_TYPE_CHOICES,
        severities=SEVERITY_CHOICES,
        statuses=FINDING_STATUS_CHOICES,
    )


def _review_vulnerability(vulnerability_id, status):
    try:
        security_service.review_vulnerability(
            vulnerability_id, current_user.id, status, get_audit_context()
        )
    except NotFoundError:
        flash("Only pending suggestions can be reviewed.", "warning")
    else:
        message = (
            "Vulnerability approved for all users."
            if status == "approved"
            else "Vulnerability suggestion rejected."
        )
        flash(message, "success" if status == "approved" else "info")
    return redirect(url_for("security.admin_vulnerabilities"))
