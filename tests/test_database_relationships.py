import json
import os
import uuid
from pathlib import Path

import pymysql
import pytest

from scripts.migrate import run_migrations
from tests.test_migrations_integration import (
    database_connection,
    drop_test_database,
    migration_config,
    require_test_name,
)

CONTRACT_PATH = Path(__file__).parent / "contracts" / "relationship_contract.json"
PERFORMANCE_INDEXES = {
    ("users", "ix_users_role_banned"),
    ("users", "ix_users_created_at"),
    ("audit_logs", "ix_audit_logs_created_at"),
    ("audit_logs", "ix_audit_logs_user_created"),
    ("categories", "ix_categories_owner_deleted_name"),
    ("categories", "ix_categories_deleted_updated"),
    ("topics", "ix_topics_owner_deleted_updated"),
    ("topics", "ix_topics_category_deleted"),
    ("topics", "ix_topics_deleted_updated"),
    ("notes", "ix_notes_owner_deleted_updated"),
    ("notes", "ix_notes_topic_owner_deleted"),
    ("notes", "ix_notes_deleted_updated"),
    ("note_access_requests", "ix_note_access_status_requested"),
    ("note_access_requests", "ix_note_access_topic_status"),
    ("lab_references", "ix_lab_references_owner_deleted_updated"),
    ("lab_references", "ix_lab_references_deleted_visibility_updated"),
    ("lab_references", "ix_lab_references_platform_deleted_updated"),
    ("lab_completions", "ix_lab_completions_user_completed"),
    ("vulnerability_catalog", "ix_vulnerability_creator_status_created"),
    ("vulnerability_catalog", "ix_vulnerability_status_active"),
    ("threat_catalog", "ix_threat_active_level_name"),
    ("security_findings", "ix_security_owner_deleted_detected"),
    ("scheduled_tasks", "ix_scheduled_user_status_due"),
    ("scheduled_tasks", "ix_scheduled_scope_status_due"),
    ("scheduled_tasks", "ix_scheduled_creator_status_updated"),
    ("scheduled_tasks", "ix_scheduled_status_due_updated"),
    ("work_logs", "ix_work_logs_owner_date"),
    ("roadmap_items", "ix_roadmap_owner_status_due"),
    ("progress_reflections", "ix_progress_owner_created"),
    ("activity_events", "ix_activity_owner_occurred"),
}


def load_relationship_contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["relationships"]


@pytest.fixture(scope="module")
def relationship_database():
    base_name = os.getenv("MIGRATION_TEST_DB_NAME", "").strip()
    if not base_name:
        pytest.skip("Set MIGRATION_TEST_DB_NAME to run relationship integration tests.")
    config = migration_config(f"{base_name}_relationships")
    require_test_name(config.DB_NAME)
    drop_test_database(config)
    try:
        run_migrations(config=config, output=lambda _message: None)
        yield config
    finally:
        drop_test_database(config)


@pytest.fixture()
def relationship_connection(relationship_database):
    connection = database_connection(relationship_database)
    connection.autocommit(False)
    connection.begin()
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def insert_user(cursor, email=None, profile_image=None):
    email = email or f"relationship-{uuid.uuid4().hex}@example.com"
    cursor.execute(
        """
        INSERT INTO users
            (email, password_hash, display_name, role, is_banned,
             mfa_secret, mfa_enabled, auth_version, failed_login_count,
             last_failed_login_at, locked_until, profile_bio, profile_image,
             created_at, updated_at)
        VALUES (%s, 'test-hash', 'Relationship User', 'user', 0,
                NULL, 0, 0, 0, NULL, NULL, NULL, %s, NOW(), NOW())
        """,
        (email, profile_image),
    )
    return cursor.lastrowid


def test_relationship_contract_documents_every_foreign_key():
    relationships = load_relationship_contract()

    assert len(relationships) == 28
    assert {item["delete_rule"] for item in relationships} == {"CASCADE", "SET NULL", "RESTRICT"}
    assert len(
        {(item["table"], item["column"]) for item in relationships}
    ) == len(relationships)


@pytest.mark.integration
def test_database_matches_frozen_relationship_contract(relationship_connection):
    expected = {
        (
            item["table"],
            item["column"],
            item["referenced_table"],
            item["referenced_column"],
            item["delete_rule"],
        )
        for item in load_relationship_contract()
    }
    with relationship_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT fk_columns.table_name AS table_name,
                   fk_columns.column_name AS column_name,
                   fk_columns.referenced_table_name AS referenced_table,
                   fk_columns.referenced_column_name AS referenced_column,
                   rules.delete_rule AS delete_rule
            FROM information_schema.key_column_usage AS fk_columns
            JOIN information_schema.referential_constraints AS rules
              ON rules.constraint_schema = fk_columns.constraint_schema
             AND rules.table_name = fk_columns.table_name
             AND rules.constraint_name = fk_columns.constraint_name
            WHERE fk_columns.table_schema = DATABASE()
              AND fk_columns.referenced_table_name IS NOT NULL
            """
        )
        actual = {
            (
                row["table_name"],
                row["column_name"],
                row["referenced_table"],
                row["referenced_column"],
                row["delete_rule"],
            )
            for row in cursor.fetchall()
        }
        cursor.execute(
            """
            SELECT table_name AS table_name, column_name AS column_name
            FROM information_schema.statistics
            WHERE table_schema = DATABASE() AND seq_in_index = 1
            """
        )
        indexed_columns = {(row["table_name"], row["column_name"]) for row in cursor.fetchall()}

    assert actual == expected
    assert {(item[0], item[1]) for item in expected}.issubset(indexed_columns)


@pytest.mark.integration
def test_cascade_removes_owner_scoped_children(relationship_connection):
    with relationship_connection.cursor() as cursor:
        user_id = insert_user(cursor)
        cursor.execute(
            """
            INSERT INTO categories
                (name, description, color, is_deleted, owner_id, created_at, updated_at)
            VALUES ('Cascade category', '', '#2563eb', 0, %s, NOW(), NOW())
            """,
            (user_id,),
        )
        category_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO topics
                (title, slug, description, status, priority, notes, is_deleted,
                 category_id, owner_id, created_at, updated_at)
            VALUES ('Cascade topic', %s, '', 'planned', 'medium', '', 0,
                    %s, %s, NOW(), NOW())
            """,
            (f"cascade-{uuid.uuid4().hex}", category_id, user_id),
        )
        topic_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO notes
                (title, body, topic_id, owner_id, is_deleted, created_at, updated_at)
            VALUES ('Cascade note', 'body', %s, %s, 0, NOW(), NOW())
            """,
            (topic_id, user_id),
        )
        note_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO contacts
                (name, email, phone, notes, is_deleted, owner_id, created_at, updated_at)
            VALUES ('Cascade contact', 'cascade@example.com', '', '', 0, %s, NOW(), NOW())
            """,
            (user_id,),
        )
        contact_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO scheduled_tasks
                (user_id, created_by, title, description, task_type, due_at,
                 status, scope, created_at, updated_at)
            VALUES (%s, %s, 'Cascade task', NULL, 'general', NULL,
                    'upcoming', 'personal', NOW(), NOW())
            """,
            (user_id, user_id),
        )
        task_id = cursor.lastrowid

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        for table_name, row_id in (
            ("categories", category_id),
            ("topics", topic_id),
            ("notes", note_id),
            ("contacts", contact_id),
            ("scheduled_tasks", task_id),
        ):
            cursor.execute(f"SELECT COUNT(*) AS total FROM `{table_name}` WHERE id = %s", (row_id,))
            assert cursor.fetchone()["total"] == 0


@pytest.mark.integration
def test_set_null_preserves_historical_and_optional_records(relationship_connection):
    with relationship_connection.cursor() as cursor:
        historical_user_id = insert_user(cursor)
        topic_owner_id = insert_user(cursor)
        cursor.execute(
            """
            INSERT INTO categories
                (name, description, color, is_deleted, owner_id, created_at, updated_at)
            VALUES ('Optional category', '', '#2563eb', 0, %s, NOW(), NOW())
            """,
            (historical_user_id,),
        )
        category_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO topics
                (title, slug, description, status, priority, notes, is_deleted,
                 category_id, owner_id, created_at, updated_at)
            VALUES ('Independent topic', %s, '', 'planned', 'medium', '', 0,
                    %s, %s, NOW(), NOW())
            """,
            (f"independent-{uuid.uuid4().hex}", category_id, topic_owner_id),
        )
        topic_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO audit_logs (action, details, ip_address, user_id, created_at)
            VALUES ('relationship_test', 'preserve', '127.0.0.1', %s, NOW())
            """,
            (historical_user_id,),
        )
        audit_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO scheduled_tasks
                (user_id, created_by, title, description, task_type, due_at,
                 status, scope, created_at, updated_at)
            VALUES (NULL, %s, 'Shared history', NULL, 'general', NULL,
                    'completed', 'global', NOW(), NOW())
            """,
            (historical_user_id,),
        )
        task_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO activity_events
                (event_type, intensity, occurred_on, owner_id, created_at, updated_at)
            VALUES ('test', 1, CURRENT_DATE, %s, NOW(), NOW())
            """,
            (historical_user_id,),
        )
        activity_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO note_access_requests
                (topic_id, note_id, requester_admin_id, status, requested_at, responded_at)
            VALUES (%s, NULL, %s, 'denied', NOW(), NOW())
            """,
            (topic_id, historical_user_id),
        )
        request_id = cursor.lastrowid

        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (historical_user_id,))

        for table_name, row_id, column_name in (
            ("topics", topic_id, "category_id"),
            ("audit_logs", audit_id, "user_id"),
            ("scheduled_tasks", task_id, "created_by"),
            ("activity_events", activity_id, "owner_id"),
            ("note_access_requests", request_id, "requester_admin_id"),
        ):
            cursor.execute(f"SELECT `{column_name}` AS value FROM `{table_name}` WHERE id = %s", (row_id,))
            assert cursor.fetchone()["value"] is None


@pytest.mark.integration
def test_restrict_prevents_deleting_referenced_parent(relationship_connection):
    with relationship_connection.cursor() as cursor:
        image_hash = "a" * 64
        cursor.execute(
            """
            INSERT INTO profile_images (image_hash, image_data, mime_type, byte_size, created_at)
            VALUES (%s, %s, 'image/png', %s, NOW())
            """,
            (image_hash, b"test-image", len(b"test-image")),
        )
        insert_user(cursor, profile_image=image_hash)

        with pytest.raises(pymysql.err.IntegrityError):
            cursor.execute("DELETE FROM profile_images WHERE image_hash = %s", (image_hash,))


@pytest.mark.integration
def test_restrict_prevents_deleting_in_use_lab_platform(relationship_connection):
    with relationship_connection.cursor() as cursor:
        user_id = insert_user(cursor)
        cursor.execute("SELECT id FROM lab_platforms WHERE slug = 'other'")
        platform_id = cursor.fetchone()["id"]
        cursor.execute(
            """
            INSERT INTO lab_references
                (name, platform_id, url, notes, topic_id, owner_id, visibility,
                 is_deleted, created_at, updated_at)
            VALUES ('Restricted platform lab', %s, 'https://example.com', '', NULL,
                    %s, 'personal', 0, NOW(), NOW())
            """,
            (platform_id, user_id),
        )

        with pytest.raises(pymysql.err.IntegrityError):
            cursor.execute("DELETE FROM lab_platforms WHERE id = %s", (platform_id,))


@pytest.mark.integration
def test_foreign_key_violation_rejects_orphan_record(relationship_connection):
    with relationship_connection.cursor() as cursor:
        with pytest.raises(pymysql.err.IntegrityError):
            cursor.execute(
                """
                INSERT INTO contacts
                    (name, email, phone, notes, is_deleted, owner_id, created_at, updated_at)
                VALUES ('Invalid owner', 'invalid@example.com', '', '', 0, 2147483647, NOW(), NOW())
                """
            )


@pytest.mark.integration
def test_unique_constraint_rejects_duplicate_email(relationship_connection):
    email = f"duplicate-{uuid.uuid4().hex}@example.com"
    with relationship_connection.cursor() as cursor:
        insert_user(cursor, email=email)
        with pytest.raises(pymysql.err.IntegrityError):
            insert_user(cursor, email=email)


@pytest.mark.integration
def test_audit_log_survives_account_deletion(relationship_connection):
    with relationship_connection.cursor() as cursor:
        user_id = insert_user(cursor)
        cursor.execute(
            """
            INSERT INTO audit_logs (action, details, ip_address, user_id, created_at)
            VALUES ('preservation_test', 'must survive', '127.0.0.1', %s, NOW())
            """,
            (user_id,),
        )
        audit_id = cursor.lastrowid
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        cursor.execute("SELECT user_id FROM audit_logs WHERE id = %s", (audit_id,))

        assert cursor.fetchone()["user_id"] is None


@pytest.mark.integration
def test_required_performance_indexes_exist(relationship_connection):
    with relationship_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT table_name AS table_name, index_name AS index_name
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            """
        )
        actual = {(row["table_name"], row["index_name"]) for row in cursor.fetchall()}

    assert PERFORMANCE_INDEXES.issubset(actual)


@pytest.mark.integration
def test_important_dashboard_and_list_queries_can_be_explained(relationship_connection):
    queries = (
        ("SELECT id FROM topics WHERE owner_id = %s AND is_deleted = 0 ORDER BY updated_at DESC", (1,)),
        ("SELECT id FROM notes WHERE owner_id = %s AND is_deleted = 0 ORDER BY updated_at DESC", (1,)),
        ("SELECT id FROM audit_logs ORDER BY created_at DESC LIMIT 25", ()),
        (
            "SELECT id FROM scheduled_tasks WHERE status = 'upcoming' "
            "AND (user_id = %s OR scope IN ('admin', 'global')) "
            "ORDER BY due_at, updated_at DESC LIMIT 4",
            (1,),
        ),
        (
            "SELECT id FROM security_findings WHERE owner_id = %s AND is_deleted = 0 "
            "ORDER BY detected_at DESC, updated_at DESC",
            (1,),
        ),
        (
            "SELECT id FROM lab_references WHERE is_deleted = 0 "
            "AND (owner_id = %s OR visibility = 'public') ORDER BY updated_at DESC",
            (1,),
        ),
    )
    with relationship_connection.cursor() as cursor:
        for query, params in queries:
            cursor.execute(f"EXPLAIN {query}", params)
            assert cursor.fetchall()
