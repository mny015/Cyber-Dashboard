from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.repositories import security_repository
from app.services import security_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from utils.audit import get_audit_context
from utils.decorators import admin_required
from utils.helpers import clean_text
from utils.security_catalog import ACTIVITY_TYPE_CHOICES, FINDING_STATUS_CHOICES, SEVERITY_CHOICES

security_bp = Blueprint("security", __name__, url_prefix="/security")


@security_bp.route("/")
@login_required
def index():
    metrics = security_repository.metrics_for_user(current_user.id)
    findings = security_repository.list_for_user(current_user.id)
    pending_suggestions = security_repository.list_pending_for_creator(current_user.id)
    return render_template(
        "security/index.html",
        metrics=metrics,
        findings=findings,
        pending_suggestions=pending_suggestions,
    )


@security_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        return save_finding()
    return render_template(
        "security/form.html",
        finding={},
        vulnerabilities=get_approved_vulnerabilities(),
        threats=get_threats(),
        activity_types=ACTIVITY_TYPE_CHOICES,
        severities=SEVERITY_CHOICES,
        statuses=FINDING_STATUS_CHOICES,
    )


@security_bp.route("/<int:finding_id>/edit", methods=["GET", "POST"])
@login_required
def edit(finding_id):
    finding = get_finding_or_404(finding_id)
    if request.method == "POST":
        return save_finding(finding_id)
    return render_template(
        "security/form.html",
        finding=finding,
        vulnerabilities=get_approved_vulnerabilities(),
        threats=get_threats(),
        activity_types=ACTIVITY_TYPE_CHOICES,
        severities=SEVERITY_CHOICES,
        statuses=FINDING_STATUS_CHOICES,
    )


@security_bp.route("/<int:finding_id>/delete", methods=["POST"])
@login_required
def delete(finding_id):
    try:
        security_service.delete_finding(
            finding_id, current_user.id, get_audit_context()
        )
    except NotFoundError:
        abort(404)
    flash("Security finding deleted.", "info")
    return redirect(url_for("security.index"))


@security_bp.route("/vulnerabilities/suggest", methods=["POST"])
@login_required
def suggest_vulnerability():
    name = clean_text(request.form.get("name"))
    category = clean_text(request.form.get("category")) or "User submitted"
    severity = clean_text(request.form.get("default_severity")) or "medium"
    description = clean_text(request.form.get("description"))
    try:
        security_service.suggest_vulnerability(
            current_user.id,
            name,
            category,
            severity,
            description,
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("security.index"))
    flash("Suggestion submitted for admin review.", "success")
    return redirect(url_for("security.index"))


@security_bp.route("/admin/vulnerabilities", methods=["GET", "POST"])
@login_required
@admin_required
def admin_vulnerabilities():
    if request.method == "POST":
        name = clean_text(request.form.get("name"))
        code = clean_text(request.form.get("code")).upper()
        category = clean_text(request.form.get("category")) or "Admin catalog"
        severity = clean_text(request.form.get("default_severity")) or "medium"
        description = clean_text(request.form.get("description"))
        try:
            security_service.save_admin_vulnerability(
                current_user.id,
                {
                    "code": code,
                    "name": name,
                    "category": category,
                    "default_severity": severity,
                    "description": description,
                },
                get_audit_context(),
            )
        except ValidationError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("security.admin_vulnerabilities"))
        flash("Vulnerability catalog entry saved.", "success")
        return redirect(url_for("security.admin_vulnerabilities"))

    return render_template(
        "security/admin_vulnerabilities.html",
        pending=get_pending_vulnerabilities(),
        vulnerabilities=get_all_vulnerabilities(),
        severities=SEVERITY_CHOICES,
    )


@security_bp.route("/admin/vulnerabilities/<int:vulnerability_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_vulnerability(vulnerability_id):
    if update_vulnerability_status(vulnerability_id, "approved"):
        flash("Vulnerability approved for all users.", "success")
    else:
        flash("Only pending suggestions can be reviewed.", "warning")
    return redirect(url_for("security.admin_vulnerabilities"))


@security_bp.route("/admin/vulnerabilities/<int:vulnerability_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_vulnerability(vulnerability_id):
    if update_vulnerability_status(vulnerability_id, "rejected"):
        flash("Vulnerability suggestion rejected.", "info")
    else:
        flash("Only pending suggestions can be reviewed.", "warning")
    return redirect(url_for("security.admin_vulnerabilities"))


def save_finding(finding_id=None):
    title = clean_text(request.form.get("title"))
    activity_type = clean_text(request.form.get("activity_type"))
    severity = clean_text(request.form.get("severity"))
    status = clean_text(request.form.get("status"))
    target = clean_text(request.form.get("target"))
    evidence = clean_text(request.form.get("evidence"))
    notes = clean_text(request.form.get("notes"))
    vulnerability_id = request.form.get("vulnerability_id", type=int) or None
    threat_id = request.form.get("threat_id", type=int) or None

    try:
        security_service.save_finding(
            current_user.id,
            {
                "vulnerability_id": vulnerability_id,
                "threat_id": threat_id,
                "activity_type": activity_type,
                "title": title,
                "target": target,
                "severity": severity,
                "status": status,
                "evidence": evidence,
                "notes": notes,
            },
            get_audit_context(),
            finding_id=finding_id,
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return redirect(request.referrer or url_for("security.create"))
    except PermissionDeniedError:
        abort(403)
    except NotFoundError:
        abort(404)

    if finding_id:
        flash("Security finding updated.", "success")
    else:
        flash("Security finding created.", "success")
    return redirect(url_for("security.index"))


def get_finding_or_404(finding_id):
    finding = security_repository.find_owned(finding_id, current_user.id)
    if not finding:
        abort(404)
    return finding


def get_approved_vulnerabilities():
    return security_repository.list_approved_vulnerabilities()


def get_all_vulnerabilities():
    return security_repository.list_all_vulnerabilities()


def get_pending_vulnerabilities():
    return security_repository.list_pending_vulnerabilities()


def get_threats():
    return security_repository.list_active_threats()


def vulnerability_is_available(vulnerability_id):
    return security_repository.vulnerability_is_available(vulnerability_id)


def threat_is_available(threat_id):
    return security_repository.threat_is_available(threat_id)


def update_vulnerability_status(vulnerability_id, status):
    try:
        security_service.review_vulnerability(
            vulnerability_id, current_user.id, status, get_audit_context()
        )
    except NotFoundError:
        return False
    return True
