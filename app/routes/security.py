from uuid import uuid4

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from utils.audit import log_audit
from utils.db import execute, fetch_all, fetch_one
from utils.decorators import admin_required
from utils.helpers import clean_text
from utils.security_catalog import ACTIVITY_TYPE_CHOICES, FINDING_STATUS_CHOICES, SEVERITY_CHOICES

security_bp = Blueprint("security", __name__, url_prefix="/security")


@security_bp.route("/")
@login_required
def index():
    metrics = fetch_one(
        """
        SELECT
            COUNT(*) AS total,
            SUM(activity_type = 'vulnerability_found') AS found_count,
            SUM(activity_type = 'vulnerability_tested') AS tested_count,
            SUM(activity_type = 'threat_managed') AS managed_count,
            SUM(severity = 'critical') AS critical_count,
            SUM(status IN ('managed', 'resolved')) AS closed_count
        FROM security_findings
        WHERE owner_id = %s AND is_deleted = 0
        """,
        (current_user.id,),
    )
    findings = fetch_all(
        """
        SELECT findings.*, vulns.name AS vulnerability_name, vulns.code AS vulnerability_code,
               threats.name AS threat_name, threats.code AS threat_code
        FROM security_findings AS findings
        LEFT JOIN vulnerability_catalog AS vulns ON vulns.id = findings.vulnerability_id
        LEFT JOIN threat_catalog AS threats ON threats.id = findings.threat_id
        WHERE findings.owner_id = %s AND findings.is_deleted = 0
        ORDER BY findings.detected_at DESC, findings.updated_at DESC
        """,
        (current_user.id,),
    )
    pending_suggestions = fetch_all(
        """
        SELECT id, code, name, category, default_severity, approval_status, created_at
        FROM vulnerability_catalog
        WHERE created_by_user_id = %s AND approval_status = 'pending'
        ORDER BY created_at DESC
        """,
        (current_user.id,),
    )
    return render_template(
        "security/index.html",
        metrics=metrics or {},
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
    finding = get_finding_or_404(finding_id)
    execute(
        """
        UPDATE security_findings
        SET is_deleted = 1, updated_at = NOW()
        WHERE id = %s AND owner_id = %s
        """,
        (finding["id"], current_user.id),
    )
    log_audit("security_finding_deleted", f"Deleted finding {finding['title']}")
    flash("Security finding deleted.", "info")
    return redirect(url_for("security.index"))


@security_bp.route("/vulnerabilities/suggest", methods=["POST"])
@login_required
def suggest_vulnerability():
    name = clean_text(request.form.get("name"))
    category = clean_text(request.form.get("category")) or "User submitted"
    severity = clean_text(request.form.get("default_severity")) or "medium"
    description = clean_text(request.form.get("description"))
    if not name or severity not in SEVERITY_CHOICES:
        flash("Provide a vulnerability name and valid severity.", "danger")
        return redirect(url_for("security.index"))

    code = f"SUG-{uuid4().hex[:10].upper()}"
    execute(
        """
        INSERT INTO vulnerability_catalog
            (code, name, category, default_severity, description, source,
             approval_status, is_active, created_by_user_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, 'User suggestion', 'pending', 0, %s, NOW(), NOW())
        """,
        (code, name, category, severity, description, current_user.id),
    )
    log_audit("vulnerability_suggested", f"Suggested vulnerability {name}")
    flash("Suggestion submitted for admin review.", "success")
    return redirect(url_for("security.index"))


@security_bp.route("/admin/vulnerabilities", methods=["GET", "POST"])
@login_required
@admin_required
def admin_vulnerabilities():
    if request.method == "POST":
        name = clean_text(request.form.get("name"))
        code = clean_text(request.form.get("code")).upper() or f"ADM-{uuid4().hex[:8].upper()}"
        category = clean_text(request.form.get("category")) or "Admin catalog"
        severity = clean_text(request.form.get("default_severity")) or "medium"
        description = clean_text(request.form.get("description"))
        if not name or severity not in SEVERITY_CHOICES:
            flash("Provide a name and valid severity.", "danger")
            return redirect(url_for("security.admin_vulnerabilities"))
        execute(
            """
            INSERT INTO vulnerability_catalog
                (code, name, category, default_severity, description, source,
                 approval_status, is_active, created_by_user_id, reviewed_by_user_id,
                 reviewed_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'Admin catalog', 'approved', 1, %s, %s, NOW(), NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                category = VALUES(category),
                default_severity = VALUES(default_severity),
                description = VALUES(description),
                approval_status = 'approved',
                is_active = 1,
                reviewed_by_user_id = VALUES(reviewed_by_user_id),
                reviewed_at = NOW(),
                updated_at = NOW()
            """,
            (code, name, category, severity, description, current_user.id, current_user.id),
        )
        log_audit("vulnerability_added", f"Admin added vulnerability {name}")
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
    if update_vulnerability_status(vulnerability_id, "approved", True):
        flash("Vulnerability approved for all users.", "success")
    else:
        flash("Only pending suggestions can be reviewed.", "warning")
    return redirect(url_for("security.admin_vulnerabilities"))


@security_bp.route("/admin/vulnerabilities/<int:vulnerability_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_vulnerability(vulnerability_id):
    if update_vulnerability_status(vulnerability_id, "rejected", False):
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

    if (
        not title
        or activity_type not in ACTIVITY_TYPE_CHOICES
        or severity not in SEVERITY_CHOICES
        or status not in FINDING_STATUS_CHOICES
    ):
        flash("Title, activity type, severity, and status are required.", "danger")
        return redirect(request.referrer or url_for("security.create"))
    if vulnerability_id and not vulnerability_is_available(vulnerability_id):
        abort(403)
    if threat_id and not threat_is_available(threat_id):
        abort(403)

    if finding_id:
        execute(
            """
            UPDATE security_findings
            SET vulnerability_id = %s, threat_id = %s, activity_type = %s,
                title = %s, target = %s, severity = %s, status = %s,
                evidence = %s, notes = %s, updated_at = NOW()
            WHERE id = %s AND owner_id = %s AND is_deleted = 0
            """,
            (
                vulnerability_id,
                threat_id,
                activity_type,
                title,
                target,
                severity,
                status,
                evidence,
                notes,
                finding_id,
                current_user.id,
            ),
        )
        log_audit("security_finding_updated", f"Updated finding {title}")
        flash("Security finding updated.", "success")
    else:
        _, finding_id = execute(
            """
            INSERT INTO security_findings
                (owner_id, vulnerability_id, threat_id, activity_type, title,
                 target, severity, status, evidence, notes, detected_at,
                 is_deleted, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 0, NOW(), NOW())
            """,
            (
                current_user.id,
                vulnerability_id,
                threat_id,
                activity_type,
                title,
                target,
                severity,
                status,
                evidence,
                notes,
            ),
        )
        log_audit("security_finding_created", f"Created finding {title}")
        flash("Security finding created.", "success")
    return redirect(url_for("security.index"))


def get_finding_or_404(finding_id):
    finding = fetch_one(
        """
        SELECT *
        FROM security_findings
        WHERE id = %s AND owner_id = %s AND is_deleted = 0
        """,
        (finding_id, current_user.id),
    )
    if not finding:
        abort(404)
    return finding


def get_approved_vulnerabilities():
    return fetch_all(
        """
        SELECT id, code, name, category, default_severity, source
        FROM vulnerability_catalog
        WHERE approval_status = 'approved' AND is_active = 1
        ORDER BY category, name
        """
    )


def get_all_vulnerabilities():
    return fetch_all(
        """
        SELECT vulns.*, users.display_name AS requested_by
        FROM vulnerability_catalog AS vulns
        LEFT JOIN users ON users.id = vulns.created_by_user_id
        ORDER BY vulns.approval_status = 'pending' DESC, vulns.category, vulns.name
        """
    )


def get_pending_vulnerabilities():
    return fetch_all(
        """
        SELECT vulns.*, users.display_name AS requested_by
        FROM vulnerability_catalog AS vulns
        LEFT JOIN users ON users.id = vulns.created_by_user_id
        WHERE vulns.approval_status = 'pending'
        ORDER BY vulns.created_at DESC
        """
    )


def get_threats():
    return fetch_all(
        """
        SELECT id, code, name, default_level, source
        FROM threat_catalog
        WHERE is_active = 1
        ORDER BY default_level = 'critical' DESC, name
        """
    )


def vulnerability_is_available(vulnerability_id):
    return bool(
        fetch_one(
            """
            SELECT id FROM vulnerability_catalog
            WHERE id = %s AND approval_status = 'approved' AND is_active = 1
            """,
            (vulnerability_id,),
        )
    )


def threat_is_available(threat_id):
    return bool(fetch_one("SELECT id FROM threat_catalog WHERE id = %s AND is_active = 1", (threat_id,)))


def update_vulnerability_status(vulnerability_id, status, is_active):
    affected, _ = execute(
        """
        UPDATE vulnerability_catalog
        SET approval_status = %s, is_active = %s, reviewed_by_user_id = %s,
            reviewed_at = NOW(), updated_at = NOW()
        WHERE id = %s AND approval_status = 'pending'
        """,
        (status, int(is_active), current_user.id, vulnerability_id),
    )
    if affected:
        log_audit("vulnerability_reviewed", f"Set vulnerability {vulnerability_id} to {status}")
    return bool(affected)
