"""HTTP handlers for findings and vulnerability catalog review."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import flash_form_errors, validate_action
from app.forms.security import (
    AdminVulnerabilityForm,
    SecurityFindingForm,
    VulnerabilitySuggestionForm,
)
from app.repositories import security_repository
from app.services import security_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.utils.audit import get_audit_context
from app.utils.decorators import (
    admin_required,
    recent_reauthentication_required,
    recent_reauthentication_required_for_writes,
    require_owned_record,
)
from app.utils.rate_limits import sensitive_action_rate_limited
from utils.security_catalog import ACTIVITY_TYPE_CHOICES, FINDING_STATUS_CHOICES, SEVERITY_CHOICES


@login_required
def index():
    return render_template(
        "security/index.html",
        metrics=security_repository.metrics_for_user(current_user.id),
        findings=security_repository.list_for_user(current_user.id),
        pending_suggestions=security_repository.list_pending_for_creator(current_user.id),
        suggestion_form=VulnerabilitySuggestionForm(),
    )


@login_required
def create():
    form, vulnerabilities, threats = _finding_form()
    if form.validate_on_submit():
        return _save_finding(form)
    return _render_finding_form(None, form, vulnerabilities, threats)


@login_required
def edit(finding_id):
    finding = _finding_or_404(finding_id)
    form, vulnerabilities, threats = _finding_form(finding)
    if form.validate_on_submit():
        return _save_finding(form, finding_id)
    return _render_finding_form(finding, form, vulnerabilities, threats)


@login_required
def delete(finding_id):
    if not validate_action():
        return redirect(url_for("security.index"))
    try:
        security_service.delete_finding(finding_id, current_user.id, get_audit_context())
    except NotFoundError:
        abort(404)
    flash("Security finding deleted.", "info")
    return redirect(url_for("security.index"))


@login_required
def suggest_vulnerability():
    form = VulnerabilitySuggestionForm()
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect(url_for("security.index", _anchor="suggest-vulnerability"))
    try:
        security_service.suggest_vulnerability(
            current_user.id,
            form.name.data,
            form.category.data,
            form.default_severity.data,
            form.description.data or "",
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("security.index"))
    flash("Suggestion submitted for admin review.", "success")
    return redirect(url_for("security.index"))


@login_required
@admin_required
@recent_reauthentication_required_for_writes
def admin_vulnerabilities():
    form = AdminVulnerabilityForm()
    if not form.validate_on_submit():
        return _render_admin_vulnerabilities(form)
    try:
        security_service.save_admin_vulnerability(
            current_user.id,
            {
                "code": form.code.data.upper(),
                "name": form.name.data,
                "category": form.category.data,
                "default_severity": form.default_severity.data,
                "description": form.description.data or "",
            },
            get_audit_context(),
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        return _render_admin_vulnerabilities(form)
    flash("Vulnerability catalog entry saved.", "success")
    return redirect(url_for("security.admin_vulnerabilities"))


@login_required
@admin_required
@recent_reauthentication_required
@sensitive_action_rate_limited
def approve_vulnerability(vulnerability_id):
    return _review_vulnerability(vulnerability_id, "approved")


@login_required
@admin_required
@recent_reauthentication_required
@sensitive_action_rate_limited
def reject_vulnerability(vulnerability_id):
    return _review_vulnerability(vulnerability_id, "rejected")


def _save_finding(form, finding_id=None):
    values = {
        "vulnerability_id": form.vulnerability_id.data,
        "threat_id": form.threat_id.data,
        "activity_type": form.activity_type.data,
        "title": form.title.data,
        "target": form.target.data or "",
        "severity": form.severity.data,
        "status": form.status.data,
        "evidence": form.evidence.data or "",
        "notes": form.notes.data or "",
    }
    try:
        security_service.save_finding(
            current_user.id, values, get_audit_context(), finding_id=finding_id
        )
    except ValidationError as exc:
        flash(str(exc), "danger")
        finding = _finding_or_404(finding_id) if finding_id else None
        vulnerabilities = security_repository.list_approved_vulnerabilities()
        threats = security_repository.list_active_threats()
        return _render_finding_form(finding, form, vulnerabilities, threats)
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
    return require_owned_record(
        security_repository.find_owned(finding_id, current_user.id)
    )


def _finding_form(finding=None):
    vulnerabilities = security_repository.list_approved_vulnerabilities()
    threats = security_repository.list_active_threats()
    form = SecurityFindingForm(obj=finding)
    form.vulnerability_id.choices = [(None, "Not linked")] + [
        (item.id, f"{item.code} - {item.name} - {item.default_severity.title()}")
        for item in vulnerabilities
    ]
    form.threat_id.choices = [(None, "Not linked")] + [
        (item.id, f"{item.code} - {item.name} - {item.default_level.title()}")
        for item in threats
    ]
    return form, vulnerabilities, threats


def _render_finding_form(finding, form, vulnerabilities, threats):
    return render_template(
        "security/form.html",
        finding=finding,
        form=form,
        vulnerabilities=vulnerabilities,
        threats=threats,
        activity_types=ACTIVITY_TYPE_CHOICES,
        severities=SEVERITY_CHOICES,
        statuses=FINDING_STATUS_CHOICES,
    )


def _review_vulnerability(vulnerability_id, status):
    if not validate_action():
        return redirect(url_for("security.admin_vulnerabilities"))
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


def _render_admin_vulnerabilities(form):
    return render_template(
        "security/admin_vulnerabilities.html",
        pending=security_repository.list_pending_vulnerabilities(),
        vulnerabilities=security_repository.list_all_vulnerabilities(),
        severities=SEVERITY_CHOICES,
        form=form,
    )
