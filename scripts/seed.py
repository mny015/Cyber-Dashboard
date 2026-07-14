"""Seed required reference catalogs after schema migrations are current."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.utils.database import DatabaseError, transaction
from app.utils.security_catalog import APP_VULNERABILITIES, THREAT_TACTICS

LAB_PLATFORMS = (
    ("picoCTF", "picoctf"),
    ("TryHackMe", "tryhackme"),
    ("Hack The Box", "hack-the-box"),
    ("PortSwigger", "portswigger"),
    ("Other", "other"),
)


def seed_database(output=print, application=None):
    application = application or create_app()
    with application.app_context():
        with transaction() as cursor:
            for name, slug in LAB_PLATFORMS:
                cursor.execute(
                    """
                    INSERT INTO lab_platforms (name, slug)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE name = VALUES(name), slug = VALUES(slug)
                    """,
                    (name, slug),
                )

            for code, name, category, severity, source in APP_VULNERABILITIES:
                cursor.execute(
                    """
                    INSERT INTO vulnerability_catalog
                        (code, name, category, default_severity, description, source,
                         approval_status, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'approved', 1, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        category = VALUES(category),
                        default_severity = VALUES(default_severity),
                        source = VALUES(source),
                        approval_status = 'approved',
                        is_active = 1,
                        updated_at = NOW()
                    """,
                    (code, name, category, severity, f"Curated catalog entry from {source}.", source),
                )

            for code, name, level in THREAT_TACTICS:
                cursor.execute(
                    """
                    INSERT INTO threat_catalog
                        (code, name, default_level, description, source,
                         is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 'MITRE ATT&CK Enterprise tactics', 1, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        default_level = VALUES(default_level),
                        source = VALUES(source),
                        is_active = 1,
                        updated_at = NOW()
                    """,
                    (code, name, level, f"MITRE ATT&CK Enterprise tactic {code}."),
                )
    output("Seed data is current.")


def main():
    try:
        seed_database()
    except (DatabaseError, RuntimeError) as exc:
        print(f"[FAIL] Seed data was not applied: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
