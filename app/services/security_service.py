"""Security finding and vulnerability-catalog write workflows."""

from uuid import uuid4

from app.models import SecurityFinding, VulnerabilityCatalogEntry
from app.repositories import security_repository
from app.services import audit_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.utils.database import db, transaction
from utils.security_catalog import ACTIVITY_TYPE_CHOICES, FINDING_STATUS_CHOICES, SEVERITY_CHOICES


def save_finding(owner_id, values, context, finding_id=None):
    _validate_finding(values)
    with transaction() as cursor:
        database = db.using(cursor)
        _validate_catalog_choices(values, database)
        finding = SecurityFinding(id=finding_id, owner_id=owner_id, **values)
        if finding_id:
            if not security_repository.find_owned(finding_id, owner_id, database=database):
                raise NotFoundError("Security finding not found.")
            security_repository.update_owned(finding, owner_id, database=database)
            action = "security_finding_updated"
            verb = "Updated"
        else:
            security_repository.create_finding(finding, database=database)
            action = "security_finding_created"
            verb = "Created"
        audit_service.record(action, f"{verb} finding {finding.title}", context, database)
    return finding


def delete_finding(finding_id, owner_id, context):
    with transaction() as cursor:
        database = db.using(cursor)
        finding = security_repository.find_owned(finding_id, owner_id, database=database)
        if not finding:
            raise NotFoundError("Security finding not found.")
        security_repository.delete_owned(finding_id, owner_id, database=database)
        audit_service.record(
            "security_finding_deleted",
            f"Deleted finding {finding.title}",
            context,
            database,
        )
    return finding


def suggest_vulnerability(owner_id, name, category, severity, description, context):
    if not name or severity not in SEVERITY_CHOICES:
        raise ValidationError("Provide a vulnerability name and valid severity.")
    entry = VulnerabilityCatalogEntry(
        code=f"SUG-{uuid4().hex[:10].upper()}",
        name=name,
        category=category or "User submitted",
        default_severity=severity,
        description=description,
        source="User suggestion",
        created_by_user_id=owner_id,
    )
    with transaction() as cursor:
        database = db.using(cursor)
        security_repository.suggest_vulnerability(entry, database=database)
        audit_service.record(
            "vulnerability_suggested",
            f"Suggested vulnerability {name}",
            context,
            database,
        )
    return entry


def save_admin_vulnerability(admin_id, values, context):
    if not values.get("name") or values.get("default_severity") not in SEVERITY_CHOICES:
        raise ValidationError("Provide a name and valid severity.")
    entry = VulnerabilityCatalogEntry(
        code=values.get("code") or f"ADM-{uuid4().hex[:8].upper()}",
        name=values["name"],
        category=values.get("category") or "Admin catalog",
        default_severity=values["default_severity"],
        description=values.get("description"),
        source="Admin catalog",
    )
    with transaction() as cursor:
        security_repository.save_admin_vulnerability(entry, admin_id, cursor=cursor)
        audit_service.record(
            "vulnerability_added",
            f"Admin added vulnerability {entry.name}",
            context,
            db.using(cursor),
        )
    return entry


def review_vulnerability(vulnerability_id, reviewer_id, status, context):
    if status not in {"approved", "rejected"}:
        raise ValidationError("Choose a valid review decision.")
    with transaction() as cursor:
        database = db.using(cursor)
        affected = security_repository.review_pending_vulnerability(
            vulnerability_id,
            reviewer_id,
            status,
            status == "approved",
            database=database,
        )
        if not affected:
            raise NotFoundError("Only pending suggestions can be reviewed.")
        audit_service.record(
            "vulnerability_reviewed",
            f"Set vulnerability {vulnerability_id} to {status}",
            context,
            database,
        )


def _validate_finding(values):
    if (
        not values.get("title")
        or values.get("activity_type") not in ACTIVITY_TYPE_CHOICES
        or values.get("severity") not in SEVERITY_CHOICES
        or values.get("status") not in FINDING_STATUS_CHOICES
    ):
        raise ValidationError("Title, activity type, severity, and status are required.")


def _validate_catalog_choices(values, database):
    vulnerability_id = values.get("vulnerability_id")
    threat_id = values.get("threat_id")
    if vulnerability_id and not security_repository.vulnerability_is_available(
        vulnerability_id, database=database
    ):
        raise PermissionDeniedError("The selected vulnerability is unavailable.")
    if threat_id and not security_repository.threat_is_available(
        threat_id, database=database
    ):
        raise PermissionDeniedError("The selected threat is unavailable.")
