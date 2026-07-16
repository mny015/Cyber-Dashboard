import re
from pathlib import Path

import pytest

from scripts.migrate import (
    DEFAULT_MIGRATIONS_DIR,
    MigrationError,
    _validate_history,
    discover_migrations,
    quote_database_identifier,
    split_sql_statements,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {
    "schema_migrations",
    "profile_images",
    "users",
    "categories",
    "contacts",
    "topics",
    "audit_logs",
    "notes",
    "note_access_requests",
    "lab_platforms",
    "lab_references",
    "lab_completions",
    "vulnerability_catalog",
    "threat_catalog",
    "security_findings",
    "scheduled_tasks",
    "work_logs",
    "roadmap_items",
    "progress_reflections",
    "activity_events",
}


def test_numbered_migrations_are_ordered_and_complete():
    migrations = discover_migrations()

    assert [migration.version for migration in migrations] == list(range(1, 29))
    assert migrations[0].filename == "001_create_schema_migrations.sql"
    assert migrations[-1].filename == "028_expand_encrypted_mfa_secret.sql"


def test_mfa_secret_column_supports_encrypted_values():
    migration = discover_migrations()[-1]

    assert migration.filename == "028_expand_encrypted_mfa_secret.sql"
    assert "MODIFY COLUMN mfa_secret VARCHAR(255) NULL" in migration.sql


def test_create_migrations_cover_every_current_table():
    table_pattern = re.compile(r"CREATE TABLE IF NOT EXISTS\s+([a-z_]+)", re.IGNORECASE)
    created_tables = set()
    for migration in discover_migrations():
        created_tables.update(table_pattern.findall(migration.sql))

    assert created_tables == EXPECTED_TABLES


def test_migration_parser_respects_comments_and_semicolons_in_strings():
    statements = split_sql_statements(
        """
        -- ignored comment; with a semicolon
        SET @query = 'SELECT ''value;still-a-string''';
        /* ignored block; comment */
        SELECT 1;
        """
    )

    assert statements == [
        "SET @query = 'SELECT ''value;still-a-string'''",
        "SELECT 1",
    ]


def test_applied_migration_checksum_changes_are_rejected():
    migrations = discover_migrations()
    first = migrations[0]

    with pytest.raises(MigrationError, match="Applied migration was modified"):
        _validate_history({first.filename: "0" * 64}, migrations)


def test_missing_applied_migration_file_is_rejected():
    with pytest.raises(MigrationError, match="missing from the repository"):
        _validate_history({"999_removed.sql": "0" * 64}, discover_migrations())


def test_database_identifier_is_strictly_validated():
    assert quote_database_identifier("cyber_dashboard_test") == "`cyber_dashboard_test`"
    with pytest.raises(MigrationError):
        quote_database_identifier("cyber-dashboard; DROP DATABASE mysql")


def test_schema_ddl_exists_only_in_numbered_sql_migrations():
    python_schema_sources = []
    for path in PROJECT_ROOT.rglob("*.py"):
        if any(part in {".git", "tests"} or part.startswith(".venv") for part in path.parts):
            continue
        source = path.read_text(encoding="utf-8").upper()
        if "CREATE TABLE" in source or "ALTER TABLE" in source:
            python_schema_sources.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert not (PROJECT_ROOT / "init_db.py").exists()
    assert not list((PROJECT_ROOT / "utils").glob("*.py"))
    assert python_schema_sources == []
    assert list(DEFAULT_MIGRATIONS_DIR.rglob("*.py")) == []
