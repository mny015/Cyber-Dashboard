"""Security finding and catalog persistence."""

from datetime import datetime

from app.models import SecurityFinding, ThreatCatalogEntry, VulnerabilityCatalogEntry
from app.utils.database import db, transaction


def metrics_for_user(owner_id):
    return db.named_query(
        "security_metrics",
        {"owner_id": int(owner_id)},
        fetch="one",
    ) or {}


def list_for_user(owner_id):
    return SecurityFinding.from_rows(
        db.named_query("security_findings_for_user", {"owner_id": int(owner_id)})
    )


def find_owned(finding_id, owner_id, database=None):
    database = database or db
    row = (
        database.table(SecurityFinding.TABLE_NAME)
        .where("id", "=", int(finding_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .first()
    )
    return SecurityFinding.from_row(row)


def create_finding(finding, database=None):
    database = database or db
    now = datetime.now()
    result = database.table(SecurityFinding.TABLE_NAME).insert(
        {
            "owner_id": finding.owner_id,
            "vulnerability_id": finding.vulnerability_id,
            "threat_id": finding.threat_id,
            "activity_type": finding.activity_type,
            "title": finding.title,
            "target": finding.target,
            "severity": finding.severity,
            "status": finding.status,
            "evidence": finding.evidence,
            "notes": finding.notes,
            "detected_at": now,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
        }
    )
    finding.id = result.last_insert_id
    return finding


def update_owned(finding, owner_id, database=None):
    database = database or db
    return (
        database.table(SecurityFinding.TABLE_NAME)
        .where("id", "=", int(finding.id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update(
            {
                "vulnerability_id": finding.vulnerability_id,
                "threat_id": finding.threat_id,
                "activity_type": finding.activity_type,
                "title": finding.title,
                "target": finding.target,
                "severity": finding.severity,
                "status": finding.status,
                "evidence": finding.evidence,
                "notes": finding.notes,
                "updated_at": datetime.now(),
            }
        )
    )


def delete_owned(finding_id, owner_id, database=None):
    database = database or db
    return (
        database.table(SecurityFinding.TABLE_NAME)
        .where("id", "=", int(finding_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update({"is_deleted": True, "updated_at": datetime.now()})
    )


def list_pending_for_creator(user_id):
    rows = (
        db.table(VulnerabilityCatalogEntry.TABLE_NAME)
        .select("id", "code", "name", "category", "default_severity", "approval_status", "created_at")
        .where("created_by_user_id", "=", int(user_id))
        .where("approval_status", "=", "pending")
        .order_by("created_at", "DESC")
        .all()
    )
    return VulnerabilityCatalogEntry.from_rows(rows)


def suggest_vulnerability(entry, database=None):
    database = database or db
    now = datetime.now()
    result = database.table(VulnerabilityCatalogEntry.TABLE_NAME).insert(
        {
            "code": entry.code,
            "name": entry.name,
            "category": entry.category,
            "default_severity": entry.default_severity,
            "description": entry.description,
            "source": entry.source,
            "approval_status": "pending",
            "is_active": False,
            "created_by_user_id": entry.created_by_user_id,
            "created_at": now,
            "updated_at": now,
        }
    )
    entry.id = result.last_insert_id
    return entry


def save_admin_vulnerability(entry, admin_id, cursor=None):
    if cursor is not None:
        return _save_admin_vulnerability(cursor, entry, admin_id)
    with transaction() as transaction_cursor:
        return _save_admin_vulnerability(transaction_cursor, entry, admin_id)


def _save_admin_vulnerability(cursor, entry, admin_id):
    cursor.execute(
            """
            INSERT INTO vulnerability_catalog
                (code, name, category, default_severity, description, source,
                 approval_status, is_active, created_by_user_id, reviewed_by_user_id,
                 reviewed_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'Admin catalog', 'approved', 1,
                    %s, %s, NOW(), NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                name = VALUES(name), category = VALUES(category),
                default_severity = VALUES(default_severity),
                description = VALUES(description), approval_status = 'approved',
                is_active = 1, reviewed_by_user_id = VALUES(reviewed_by_user_id),
                reviewed_at = NOW(), updated_at = NOW()
            """,
            (
                entry.code,
                entry.name,
                entry.category,
                entry.default_severity,
                entry.description,
                int(admin_id),
                int(admin_id),
            ),
    )
    return cursor.lastrowid


def list_approved_vulnerabilities():
    rows = (
        db.table(VulnerabilityCatalogEntry.TABLE_NAME)
        .where("approval_status", "=", "approved")
        .where("is_active", "=", True)
        .order_by("category", "ASC")
        .order_by("name", "ASC")
        .all()
    )
    return VulnerabilityCatalogEntry.from_rows(rows)


def list_all_vulnerabilities():
    return VulnerabilityCatalogEntry.from_rows(db.named_query("vulnerability_catalog_all"))


def list_pending_vulnerabilities():
    return VulnerabilityCatalogEntry.from_rows(db.named_query("vulnerability_catalog_pending"))


def list_active_threats():
    rows = db.named_query("active_threats")
    return ThreatCatalogEntry.from_rows(rows)


def vulnerability_is_available(vulnerability_id, database=None):
    database = database or db
    return (
        database.table(VulnerabilityCatalogEntry.TABLE_NAME)
        .where("id", "=", int(vulnerability_id))
        .where("approval_status", "=", "approved")
        .where("is_active", "=", True)
        .exists()
    )


def threat_is_available(threat_id, database=None):
    database = database or db
    return (
        database.table(ThreatCatalogEntry.TABLE_NAME)
        .where("id", "=", int(threat_id))
        .where("is_active", "=", True)
        .exists()
    )


def review_pending_vulnerability(
    vulnerability_id, reviewer_id, status, is_active, database=None
):
    database = database or db
    result = (
        database.table(VulnerabilityCatalogEntry.TABLE_NAME)
        .where("id", "=", int(vulnerability_id))
        .where("approval_status", "=", "pending")
        .update(
            {
                "approval_status": status,
                "is_active": bool(is_active),
                "reviewed_by_user_id": int(reviewer_id),
                "reviewed_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        )
    )
    return result.affected_rows
