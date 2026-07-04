"""Add security findings and catalog

Revision ID: a5c9f71d22b0
Revises: e31a0b8c92d4
Create Date: 2026-06-19 10:00:00.000000

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "a5c9f71d22b0"
down_revision = "e31a0b8c92d4"
branch_labels = None
depends_on = None
SEED_TIME = datetime(2026, 6, 19, 10, 0)


APP_VULNERABILITIES = [
    ("A01:2025", "Broken Access Control", "Web Application", "critical", "OWASP Top 10:2025"),
    ("A02:2025", "Security Misconfiguration", "Web Application", "high", "OWASP Top 10:2025"),
    ("A03:2025", "Software Supply Chain Failures", "Web Application", "critical", "OWASP Top 10:2025"),
    ("A04:2025", "Cryptographic Failures", "Web Application", "high", "OWASP Top 10:2025"),
    ("A05:2025", "Injection", "Web Application", "critical", "OWASP Top 10:2025"),
    ("A06:2025", "Insecure Design", "Web Application", "high", "OWASP Top 10:2025"),
    ("A07:2025", "Authentication Failures", "Web Application", "high", "OWASP Top 10:2025"),
    ("A08:2025", "Software or Data Integrity Failures", "Web Application", "high", "OWASP Top 10:2025"),
    ("A09:2025", "Security Logging and Alerting Failures", "Web Application", "medium", "OWASP Top 10:2025"),
    ("A10:2025", "Mishandling of Exceptional Conditions", "Web Application", "medium", "OWASP Top 10:2025"),
    ("API1:2023", "Broken Object Level Authorization", "API Security", "critical", "OWASP API Security Top 10:2023"),
    ("API2:2023", "Broken Authentication", "API Security", "critical", "OWASP API Security Top 10:2023"),
    ("API3:2023", "Broken Object Property Level Authorization", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API4:2023", "Unrestricted Resource Consumption", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API5:2023", "Broken Function Level Authorization", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API6:2023", "Unrestricted Access to Sensitive Business Flows", "API Security", "medium", "OWASP API Security Top 10:2023"),
    ("API7:2023", "Server Side Request Forgery", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API8:2023", "Security Misconfiguration", "API Security", "high", "OWASP API Security Top 10:2023"),
    ("API9:2023", "Improper Inventory Management", "API Security", "medium", "OWASP API Security Top 10:2023"),
    ("API10:2023", "Unsafe Consumption of APIs", "API Security", "medium", "OWASP API Security Top 10:2023"),
    ("VAPT-XSS", "Cross-Site Scripting", "Common VAPT", "high", "Common web security testing category"),
    ("VAPT-CSRF", "Cross-Site Request Forgery", "Common VAPT", "medium", "Common web security testing category"),
    ("VAPT-PATH", "Path Traversal", "Common VAPT", "high", "Common web security testing category"),
    ("VAPT-FILE", "Unrestricted File Upload", "Common VAPT", "high", "Common web security testing category"),
    ("VAPT-DESER", "Insecure Deserialization", "Common VAPT", "critical", "Common web security testing category"),
]


THREAT_TACTICS = [
    ("TA0043", "Reconnaissance", "medium"),
    ("TA0042", "Resource Development", "medium"),
    ("TA0001", "Initial Access", "critical"),
    ("TA0002", "Execution", "high"),
    ("TA0003", "Persistence", "high"),
    ("TA0004", "Privilege Escalation", "critical"),
    ("TA0005", "Stealth", "high"),
    ("TA0112", "Defense Impairment", "critical"),
    ("TA0006", "Credential Access", "critical"),
    ("TA0007", "Discovery", "medium"),
    ("TA0008", "Lateral Movement", "critical"),
    ("TA0009", "Collection", "high"),
    ("TA0011", "Command and Control", "critical"),
    ("TA0010", "Exfiltration", "critical"),
    ("TA0040", "Impact", "critical"),
]


def upgrade():
    vulnerability_catalog = op.create_table(
        "vulnerability_catalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("default_severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=160), nullable=False),
        sa.Column("approval_status", sa.String(length=20), nullable=False, server_default="approved"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_vulnerability_code"),
    )
    op.create_index("ix_vulnerability_status", "vulnerability_catalog", ["approval_status"])

    threat_catalog = op.create_table(
        "threat_catalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("default_level", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=160), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_threat_code"),
    )

    op.create_table(
        "security_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("vulnerability_id", sa.Integer(), nullable=True),
        sa.Column("threat_id", sa.Integer(), nullable=True),
        sa.Column("activity_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vulnerability_id"], ["vulnerability_catalog.id"]),
        sa.ForeignKeyConstraint(["threat_id"], ["threat_catalog.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_findings_owner_id", "security_findings", ["owner_id"])
    op.create_index("ix_security_findings_vulnerability_id", "security_findings", ["vulnerability_id"])
    op.create_index("ix_security_findings_threat_id", "security_findings", ["threat_id"])

    op.bulk_insert(
        vulnerability_catalog,
        [
            {
                "code": code,
                "name": name,
                "category": category,
                "default_severity": severity,
                "description": f"Curated catalog entry from {source}.",
                "source": source,
                "approval_status": "approved",
                "is_active": True,
                "created_at": SEED_TIME,
                "updated_at": SEED_TIME,
            }
            for code, name, category, severity, source in APP_VULNERABILITIES
        ],
    )
    op.bulk_insert(
        threat_catalog,
        [
            {
                "code": code,
                "name": name,
                "default_level": level,
                "description": f"MITRE ATT&CK Enterprise tactic {code}.",
                "source": "MITRE ATT&CK Enterprise tactics",
                "is_active": True,
                "created_at": SEED_TIME,
                "updated_at": SEED_TIME,
            }
            for code, name, level in THREAT_TACTICS
        ],
    )


def downgrade():
    op.drop_table("security_findings")
    op.drop_index("ix_vulnerability_status", table_name="vulnerability_catalog")
    op.drop_table("threat_catalog")
    op.drop_table("vulnerability_catalog")
