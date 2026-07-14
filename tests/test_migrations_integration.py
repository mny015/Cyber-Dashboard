import json
import os
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pymysql
import pytest
from pymysql.cursors import DictCursor

from scripts.migrate import run_migrations

CONTRACT_PATH = Path(__file__).parent / "contracts" / "schema_contract.json"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAFE_TEST_NAME = re.compile(r"^[A-Za-z0-9_]*migration_test[A-Za-z0-9_]*$", re.IGNORECASE)


def migration_config(database_name):
    required = {
        "DB_HOST": os.getenv("MIGRATION_DB_HOST") or os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("MIGRATION_DB_PORT") or os.getenv("DB_PORT", "3306"),
        "DB_USER": os.getenv("MIGRATION_DB_USER") or os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("MIGRATION_DB_PASSWORD") or os.getenv("DB_PASSWORD"),
        "DB_CHARSET": os.getenv("MIGRATION_DB_CHARSET")
        or os.getenv("DB_CHARSET", "utf8mb4"),
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        pytest.skip("Set migration test database credentials: " + ", ".join(missing))
    return SimpleNamespace(DB_NAME=database_name, **required)


def server_connection(config):
    return pymysql.connect(
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        charset=config.DB_CHARSET,
        autocommit=True,
        cursorclass=DictCursor,
    )


def database_connection(config):
    return pymysql.connect(
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset=config.DB_CHARSET,
        autocommit=True,
        cursorclass=DictCursor,
    )


def require_test_name(name):
    if not SAFE_TEST_NAME.fullmatch(name):
        pytest.fail("Migration test databases must contain 'migration_test' and use safe characters.")
    return f"`{name}`"


def drop_test_database(config):
    quoted_name = require_test_name(config.DB_NAME)
    connection = server_connection(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {quoted_name}")
    finally:
        connection.close()


def fetch_table_names(config):
    connection = database_connection(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            return {next(iter(row.values())) for row in cursor.fetchall()}
    finally:
        connection.close()


def assert_schema_contract(config):
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["tables"]
    connection = database_connection(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name AS table_name,
                       column_name AS column_name,
                       data_type AS data_type,
                       is_nullable AS is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s
                """,
                (config.DB_NAME,),
            )
            column_rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT table_name AS table_name,
                       index_name AS index_name,
                       non_unique AS non_unique,
                       column_name AS column_name,
                       seq_in_index AS sequence_number
                FROM information_schema.statistics
                WHERE table_schema = %s
                ORDER BY table_name, index_name, seq_in_index
                """,
                (config.DB_NAME,),
            )
            index_rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT table_name AS table_name,
                       constraint_name AS constraint_name,
                       column_name AS column_name,
                       referenced_table_name AS referenced_table,
                       referenced_column_name AS referenced_column,
                       ordinal_position AS sequence_number
                FROM information_schema.key_column_usage
                WHERE table_schema = %s AND referenced_table_name IS NOT NULL
                ORDER BY table_name, constraint_name, ordinal_position
                """,
                (config.DB_NAME,),
            )
            foreign_key_rows = cursor.fetchall()
    finally:
        connection.close()

    actual_columns = {}
    for row in column_rows:
        actual_columns.setdefault(row["table_name"], {})[row["column_name"]] = {
            "type": row["data_type"].lower(),
            "nullable": row["is_nullable"] == "YES",
        }
    actual_indexes = {}
    index_uniqueness = {}
    for row in index_rows:
        table_indexes = actual_indexes.setdefault(row["table_name"], {})
        table_indexes.setdefault(row["index_name"], []).append(row["column_name"])
        index_uniqueness.setdefault(row["table_name"], {})[row["index_name"]] = not bool(
            row["non_unique"]
        )
    foreign_keys = {}
    for row in foreign_key_rows:
        table_keys = foreign_keys.setdefault(row["table_name"], {})
        key = table_keys.setdefault(
            row["constraint_name"],
            {"columns": [], "referenced_columns": []},
        )
        key["columns"].append(row["column_name"])
        key["referenced_table"] = row["referenced_table"]
        key["referenced_columns"].append(row["referenced_column"])

    assert set(actual_columns) == set(contract) | {"schema_migrations"}
    for table_name, expected_table in contract.items():
        assert actual_columns[table_name] == expected_table["columns"]
        assert actual_indexes[table_name]["PRIMARY"] == expected_table["primary_key"]
        for index_name, expected_columns in expected_table["unique_indexes"].items():
            assert actual_indexes[table_name][index_name] == expected_columns
            assert index_uniqueness[table_name][index_name]
        for index_name, expected_columns in expected_table["indexes"].items():
            assert actual_indexes[table_name][index_name] == expected_columns
        actual_foreign_keys = list(foreign_keys.get(table_name, {}).values())
        for expected_foreign_key in expected_table["foreign_keys"]:
            assert expected_foreign_key in actual_foreign_keys


def clone_existing_database(source_name, target_config):
    if not re.fullmatch(r"[A-Za-z0-9_]+", source_name):
        pytest.fail("MIGRATION_EXISTING_SOURCE_DB_NAME contains unsafe characters.")
    if source_name == target_config.DB_NAME:
        pytest.fail("Migration source and target databases must be different.")

    source_config = migration_config(source_name)
    source_connection = database_connection(source_config)
    target_connection = database_connection(target_config)
    row_counts = {}
    try:
        with source_connection.cursor() as source_cursor, target_connection.cursor() as target_cursor:
            source_cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
            table_names = [next(iter(row.values())) for row in source_cursor.fetchall()]
            table_names = [name for name in table_names if name != "schema_migrations"]
            target_cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table_name in table_names:
                if not re.fullmatch(r"[A-Za-z0-9_]+", table_name):
                    pytest.fail(f"Unsafe source table name: {table_name}")
                target_cursor.execute(
                    f"CREATE TABLE `{target_config.DB_NAME}`.`{table_name}` "
                    f"LIKE `{source_name}`.`{table_name}`"
                )
                target_cursor.execute(
                    f"INSERT INTO `{target_config.DB_NAME}`.`{table_name}` "
                    f"SELECT * FROM `{source_name}`.`{table_name}`"
                )
                if table_name != "alembic_version":
                    source_cursor.execute(
                        f"SELECT COUNT(*) AS total FROM `{source_name}`.`{table_name}`"
                    )
                    row_counts[table_name] = source_cursor.fetchone()["total"]
            target_cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    finally:
        source_connection.close()
        target_connection.close()
    return row_counts


def fetch_row_counts(config, table_names):
    connection = database_connection(config)
    try:
        with connection.cursor() as cursor:
            counts = {}
            for table_name in table_names:
                cursor.execute(f"SELECT COUNT(*) AS total FROM `{table_name}`")
                counts[table_name] = cursor.fetchone()["total"]
            return counts
    finally:
        connection.close()


def fetch_legacy_fixture(config):
    connection = database_connection(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT users.email, categories.name AS category_name,
                       topics.title AS topic_title, topics.slug AS topic_slug
                FROM users
                JOIN categories ON categories.owner_id = users.id
                JOIN topics
                  ON topics.owner_id = users.id
                 AND topics.category_id = categories.id
                WHERE users.email = %s
                """,
                ("legacy-migration@example.com",),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def seed_existing_database(config):
    connection = database_connection(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users
                    (email, password_hash, display_name, role, is_banned,
                     mfa_enabled, auth_version, created_at, updated_at)
                VALUES ('legacy-migration@example.com', 'legacy-test-hash',
                        'Legacy Migration User', 'user', 0, 0, 0, NOW(), NOW())
                """
            )
            user_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO categories
                    (name, description, color, is_deleted, owner_id, created_at, updated_at)
                VALUES ('Legacy Category', '', '#2563eb', 0, %s, NOW(), NOW())
                """,
                (user_id,),
            )
            category_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO topics
                    (title, slug, description, status, priority, notes, is_deleted,
                     category_id, owner_id, created_at, updated_at)
                VALUES ('Legacy Topic', 'legacy-topic', '', 'planned', 'medium', '', 0,
                        %s, %s, NOW(), NOW())
                """,
                (category_id, user_id),
            )
    finally:
        connection.close()


def explain_important_queries(config):
    queries = {
        "topics_list": (
            "SELECT id FROM topics WHERE owner_id = %s AND is_deleted = 0 "
            "ORDER BY updated_at DESC",
            (1,),
        ),
        "notes_list": (
            "SELECT id FROM notes WHERE owner_id = %s AND is_deleted = 0 "
            "ORDER BY updated_at DESC",
            (1,),
        ),
        "audit_list": ("SELECT id FROM audit_logs ORDER BY created_at DESC LIMIT 25", ()),
        "scheduled_dashboard": (
            "SELECT id FROM scheduled_tasks WHERE status = 'upcoming' "
            "AND (user_id = %s OR scope IN ('admin', 'global')) "
            "ORDER BY due_at, updated_at DESC LIMIT 4",
            (1,),
        ),
        "findings_list": (
            "SELECT id FROM security_findings WHERE owner_id = %s AND is_deleted = 0 "
            "ORDER BY detected_at DESC, updated_at DESC",
            (1,),
        ),
        "labs_list": (
            "SELECT id FROM lab_references WHERE is_deleted = 0 "
            "AND (owner_id = %s OR visibility = 'public') ORDER BY updated_at DESC",
            (1,),
        ),
    }
    connection = database_connection(config)
    try:
        with connection.cursor() as cursor:
            plans = {}
            for name, (query, params) in queries.items():
                cursor.execute(f"EXPLAIN {query}", params)
                plans[name] = [
                    {
                        "table": row.get("table"),
                        "access_type": row.get("type"),
                        "key": row.get("key"),
                        "rows": row.get("rows"),
                        "extra": row.get("Extra"),
                    }
                    for row in cursor.fetchall()
                ]
            return plans
    finally:
        connection.close()


@pytest.mark.integration
def test_migrations_build_clean_database_and_never_rerun():
    base_name = os.getenv("MIGRATION_TEST_DB_NAME", "").strip()
    if not base_name:
        pytest.skip("Set MIGRATION_TEST_DB_NAME to run destructive migration integration tests.")
    config = migration_config(f"{base_name}_clean")
    require_test_name(config.DB_NAME)
    drop_test_database(config)
    try:
        first_result = run_migrations(config=config, output=lambda _message: None)
        second_result = run_migrations(config=config, output=lambda _message: None)

        assert len(first_result.applied) == 27
        assert first_result.skipped == ()
        assert second_result.applied == ()
        assert len(second_result.skipped) == 27
        assert "schema_migrations" in fetch_table_names(config)
        assert_schema_contract(config)
    finally:
        drop_test_database(config)


@pytest.mark.integration
def test_migrations_preserve_copy_of_existing_database(tmp_path):
    base_name = os.getenv("MIGRATION_TEST_DB_NAME", "").strip()
    if not base_name:
        pytest.skip("Set MIGRATION_TEST_DB_NAME to run destructive migration integration tests.")
    source_name = f"{base_name}_legacy_source"
    source_config = migration_config(source_name)
    config = migration_config(f"{base_name}_existing")
    require_test_name(source_config.DB_NAME)
    require_test_name(config.DB_NAME)
    drop_test_database(source_config)
    drop_test_database(config)
    try:
        legacy_migrations = tmp_path / "legacy_migrations"
        legacy_migrations.mkdir()
        for migration_path in sorted((PROJECT_ROOT / "migrations").glob("*.sql")):
            if int(migration_path.name[:3]) <= 17:
                shutil.copy2(migration_path, legacy_migrations / migration_path.name)
        run_migrations(
            config=source_config,
            migrations_dir=legacy_migrations,
            output=lambda _message: None,
        )
        seed_existing_database(source_config)

        server = server_connection(config)
        try:
            with server.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE {require_test_name(config.DB_NAME)} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        finally:
            server.close()

        before_counts = clone_existing_database(source_name, config)
        run_migrations(config=config, output=lambda _message: None)
        after_counts = fetch_row_counts(config, before_counts)

        assert all(
            after_counts[table_name] >= before_count
            for table_name, before_count in before_counts.items()
        )
        assert after_counts["lab_platforms"] == 5
        assert fetch_legacy_fixture(config) == {
            "email": "legacy-migration@example.com",
            "category_name": "Legacy Category",
            "topic_title": "Legacy Topic",
            "topic_slug": "legacy-topic",
        }
        assert "alembic_version" not in fetch_table_names(config)
        assert_schema_contract(config)
        plans = explain_important_queries(config)
        assert all(plans.values())
        if os.getenv("SHOW_EXPLAIN_PLANS") == "1":
            print(json.dumps(plans, indent=2, default=str))
    finally:
        drop_test_database(config)
        drop_test_database(source_config)
