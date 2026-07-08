"""Plain-Python schema registry for the Cyber Dashboard database.

This module is the coursework schema source of truth. It intentionally uses
dataclasses and dictionaries instead of an ORM, so runtime code can keep using
PyMySQL with parameterized SQL.
"""

from dataclasses import dataclass
import re
from typing import Sequence


@dataclass(frozen=True)
class SchemaTable:
    name: str
    purpose: str
    columns: tuple[str, ...]
    primary_key: tuple[str, ...]
    create_sql: str
    foreign_keys: tuple[str, ...] = ()
    indexes: tuple[str, ...] = ()
    allowed_insert_columns: tuple[str, ...] = ()
    allowed_update_columns: tuple[str, ...] = ()


TABLES = (
    SchemaTable(
        name="profile_images",
        purpose="Stores validated profile image bytes by SHA-256 hash so user uploads are not served from static paths.",
        columns=("image_hash", "image_data", "mime_type", "byte_size", "created_at"),
        primary_key=("image_hash",),
        create_sql="""
        CREATE TABLE IF NOT EXISTS profile_images (
            image_hash CHAR(64) NOT NULL,
            image_data LONGBLOB NOT NULL,
            mime_type VARCHAR(80) NOT NULL,
            byte_size INT NOT NULL,
            created_at DATETIME NOT NULL,
            PRIMARY KEY (image_hash)
        )
        """,
        allowed_insert_columns=("image_hash", "image_data", "mime_type", "byte_size", "created_at"),
        allowed_update_columns=("image_data", "mime_type", "byte_size"),
    ),
    SchemaTable(
        name="lab_platforms",
        purpose="Normalizes lab providers such as picoCTF, TryHackMe, Hack The Box, PortSwigger, and Other.",
        columns=("id", "name", "slug"),
        primary_key=("id",),
        indexes=("uq_lab_platform_name", "uq_lab_platform_slug"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS lab_platforms (
            id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(120) NOT NULL,
            slug VARCHAR(120) NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_lab_platform_name (name),
            UNIQUE KEY uq_lab_platform_slug (slug)
        )
        """,
        allowed_insert_columns=("name", "slug"),
        allowed_update_columns=("name", "slug"),
    ),
    SchemaTable(
        name="users",
        purpose="Stores accounts, roles, login hardening fields, MFA settings, and profile metadata.",
        columns=(
            "id",
            "email",
            "password_hash",
            "display_name",
            "role",
            "is_banned",
            "mfa_secret",
            "mfa_enabled",
            "auth_version",
            "failed_login_count",
            "last_failed_login_at",
            "locked_until",
            "profile_bio",
            "profile_image",
            "created_at",
            "updated_at",
        ),
        primary_key=("id",),
        foreign_keys=("profile_image -> profile_images.image_hash",),
        indexes=("uq_users_email",),
        create_sql="""
        CREATE TABLE IF NOT EXISTS users (
            id INT NOT NULL AUTO_INCREMENT,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            display_name VARCHAR(120) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            is_banned BOOLEAN NOT NULL DEFAULT FALSE,
            mfa_secret VARCHAR(64) NULL,
            mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            auth_version INT NOT NULL DEFAULT 0,
            failed_login_count INT NOT NULL DEFAULT 0,
            last_failed_login_at DATETIME NULL,
            locked_until DATETIME NULL,
            profile_bio TEXT NULL,
            profile_image CHAR(64) NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_users_email (email),
            CONSTRAINT fk_users_profile_image FOREIGN KEY (profile_image) REFERENCES profile_images(image_hash)
        )
        """,
        allowed_insert_columns=(
            "email",
            "password_hash",
            "display_name",
            "role",
            "is_banned",
            "mfa_secret",
            "mfa_enabled",
            "auth_version",
            "failed_login_count",
            "last_failed_login_at",
            "locked_until",
            "profile_bio",
            "profile_image",
            "created_at",
            "updated_at",
        ),
        allowed_update_columns=(
            "email",
            "password_hash",
            "display_name",
            "role",
            "is_banned",
            "mfa_secret",
            "mfa_enabled",
            "auth_version",
            "failed_login_count",
            "last_failed_login_at",
            "locked_until",
            "profile_bio",
            "profile_image",
            "updated_at",
        ),
    ),
    SchemaTable(
        name="vulnerability_catalog",
        purpose="Stores approved and pending vulnerability definitions used by security finding records.",
        columns=(
            "id",
            "code",
            "name",
            "category",
            "default_severity",
            "description",
            "source",
            "approval_status",
            "is_active",
            "created_by_user_id",
            "reviewed_by_user_id",
            "reviewed_at",
            "created_at",
            "updated_at",
        ),
        primary_key=("id",),
        foreign_keys=("created_by_user_id -> users.id", "reviewed_by_user_id -> users.id"),
        indexes=("uq_vulnerability_code", "ix_vulnerability_status"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS vulnerability_catalog (
            id INT NOT NULL AUTO_INCREMENT,
            code VARCHAR(40) NOT NULL,
            name VARCHAR(200) NOT NULL,
            category VARCHAR(120) NOT NULL,
            default_severity VARCHAR(20) NOT NULL DEFAULT 'medium',
            description TEXT NOT NULL,
            source VARCHAR(160) NOT NULL,
            approval_status VARCHAR(20) NOT NULL DEFAULT 'approved',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_by_user_id INT NULL,
            reviewed_by_user_id INT NULL,
            reviewed_at DATETIME NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_vulnerability_code (code),
            KEY ix_vulnerability_status (approval_status),
            CONSTRAINT fk_vulnerability_created_by FOREIGN KEY (created_by_user_id) REFERENCES users(id),
            CONSTRAINT fk_vulnerability_reviewed_by FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id)
        )
        """,
        allowed_insert_columns=(
            "code",
            "name",
            "category",
            "default_severity",
            "description",
            "source",
            "approval_status",
            "is_active",
            "created_by_user_id",
            "reviewed_by_user_id",
            "reviewed_at",
            "created_at",
            "updated_at",
        ),
        allowed_update_columns=(
            "code",
            "name",
            "category",
            "default_severity",
            "description",
            "source",
            "approval_status",
            "is_active",
            "created_by_user_id",
            "reviewed_by_user_id",
            "reviewed_at",
            "updated_at",
        ),
    ),
    SchemaTable(
        name="threat_catalog",
        purpose="Stores threat/tactic choices and default levels for classifying security work.",
        columns=(
            "id",
            "code",
            "name",
            "default_level",
            "description",
            "source",
            "is_active",
            "created_at",
            "updated_at",
        ),
        primary_key=("id",),
        indexes=("uq_threat_code",),
        create_sql="""
        CREATE TABLE IF NOT EXISTS threat_catalog (
            id INT NOT NULL AUTO_INCREMENT,
            code VARCHAR(40) NOT NULL,
            name VARCHAR(200) NOT NULL,
            default_level VARCHAR(20) NOT NULL DEFAULT 'medium',
            description TEXT NOT NULL,
            source VARCHAR(160) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_threat_code (code)
        )
        """,
        allowed_insert_columns=(
            "code",
            "name",
            "default_level",
            "description",
            "source",
            "is_active",
            "created_at",
            "updated_at",
        ),
        allowed_update_columns=("code", "name", "default_level", "description", "source", "is_active", "updated_at"),
    ),
    SchemaTable(
        name="security_findings",
        purpose="Stores user-owned vulnerability testing, findings, managed threats, evidence, and notes.",
        columns=(
            "id",
            "owner_id",
            "vulnerability_id",
            "threat_id",
            "activity_type",
            "title",
            "target",
            "severity",
            "status",
            "evidence",
            "notes",
            "detected_at",
            "is_deleted",
            "created_at",
            "updated_at",
        ),
        primary_key=("id",),
        foreign_keys=(
            "owner_id -> users.id",
            "vulnerability_id -> vulnerability_catalog.id",
            "threat_id -> threat_catalog.id",
        ),
        indexes=("ix_security_findings_owner_id", "ix_security_findings_vulnerability_id", "ix_security_findings_threat_id"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS security_findings (
            id INT NOT NULL AUTO_INCREMENT,
            owner_id INT NOT NULL,
            vulnerability_id INT NULL,
            threat_id INT NULL,
            activity_type VARCHAR(40) NOT NULL,
            title VARCHAR(200) NOT NULL,
            target VARCHAR(255) NOT NULL,
            severity VARCHAR(20) NOT NULL DEFAULT 'medium',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            evidence TEXT NOT NULL,
            notes TEXT NOT NULL,
            detected_at DATETIME NOT NULL,
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            KEY ix_security_findings_owner_id (owner_id),
            KEY ix_security_findings_vulnerability_id (vulnerability_id),
            KEY ix_security_findings_threat_id (threat_id),
            CONSTRAINT fk_security_findings_owner FOREIGN KEY (owner_id) REFERENCES users(id),
            CONSTRAINT fk_security_findings_vulnerability FOREIGN KEY (vulnerability_id) REFERENCES vulnerability_catalog(id),
            CONSTRAINT fk_security_findings_threat FOREIGN KEY (threat_id) REFERENCES threat_catalog(id)
        )
        """,
        allowed_insert_columns=(
            "owner_id",
            "vulnerability_id",
            "threat_id",
            "activity_type",
            "title",
            "target",
            "severity",
            "status",
            "evidence",
            "notes",
            "detected_at",
            "is_deleted",
            "created_at",
            "updated_at",
        ),
        allowed_update_columns=(
            "vulnerability_id",
            "threat_id",
            "activity_type",
            "title",
            "target",
            "severity",
            "status",
            "evidence",
            "notes",
            "detected_at",
            "is_deleted",
            "updated_at",
        ),
    ),
    SchemaTable(
        name="categories",
        purpose="Stores per-user category labels for grouping topics.",
        columns=("id", "name", "description", "color", "is_deleted", "owner_id", "created_at", "updated_at"),
        primary_key=("id",),
        foreign_keys=("owner_id -> users.id",),
        indexes=("uq_category_owner_name", "ix_categories_owner_id"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS categories (
            id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(120) NOT NULL,
            description TEXT NOT NULL,
            color VARCHAR(32) NOT NULL DEFAULT '#2563eb',
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            owner_id INT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_category_owner_name (owner_id, name),
            KEY ix_categories_owner_id (owner_id),
            CONSTRAINT fk_categories_owner FOREIGN KEY (owner_id) REFERENCES users(id)
        )
        """,
        allowed_insert_columns=("name", "description", "color", "is_deleted", "owner_id", "created_at", "updated_at"),
        allowed_update_columns=("name", "description", "color", "is_deleted", "updated_at"),
    ),
    SchemaTable(
        name="contacts",
        purpose="Stores per-user contact records used for CRUD practice and personal reference.",
        columns=("id", "name", "email", "phone", "notes", "is_deleted", "owner_id", "created_at", "updated_at"),
        primary_key=("id",),
        foreign_keys=("owner_id -> users.id",),
        indexes=("ix_contacts_owner_id",),
        create_sql="""
        CREATE TABLE IF NOT EXISTS contacts (
            id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(40) NOT NULL,
            notes TEXT NOT NULL,
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            owner_id INT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            KEY ix_contacts_owner_id (owner_id),
            CONSTRAINT fk_contacts_owner FOREIGN KEY (owner_id) REFERENCES users(id)
        )
        """,
        allowed_insert_columns=("name", "email", "phone", "notes", "is_deleted", "owner_id", "created_at", "updated_at"),
        allowed_update_columns=("name", "email", "phone", "notes", "is_deleted", "updated_at"),
    ),
    SchemaTable(
        name="topics",
        purpose="Stores per-user learning topics with category links, progress status, priority, and notes.",
        columns=(
            "id",
            "title",
            "slug",
            "description",
            "status",
            "priority",
            "notes",
            "is_deleted",
            "category_id",
            "owner_id",
            "created_at",
            "updated_at",
        ),
        primary_key=("id",),
        foreign_keys=("category_id -> categories.id", "owner_id -> users.id"),
        indexes=("uq_topic_owner_slug", "ix_topics_owner_id"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS topics (
            id INT NOT NULL AUTO_INCREMENT,
            title VARCHAR(200) NOT NULL,
            slug VARCHAR(220) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(40) NOT NULL DEFAULT 'planned',
            priority VARCHAR(40) NOT NULL DEFAULT 'medium',
            notes TEXT NOT NULL,
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            category_id INT NULL,
            owner_id INT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_topic_owner_slug (owner_id, slug),
            KEY ix_topics_owner_id (owner_id),
            CONSTRAINT fk_topics_category FOREIGN KEY (category_id) REFERENCES categories(id),
            CONSTRAINT fk_topics_owner FOREIGN KEY (owner_id) REFERENCES users(id)
        )
        """,
        allowed_insert_columns=(
            "title",
            "slug",
            "description",
            "status",
            "priority",
            "notes",
            "is_deleted",
            "category_id",
            "owner_id",
            "created_at",
            "updated_at",
        ),
        allowed_update_columns=(
            "title",
            "slug",
            "description",
            "status",
            "priority",
            "notes",
            "is_deleted",
            "category_id",
            "updated_at",
        ),
    ),
    SchemaTable(
        name="audit_logs",
        purpose="Stores timestamped evidence for auth, admin, lab, backup, security, and CRUD actions.",
        columns=("id", "action", "details", "ip_address", "user_id", "created_at"),
        primary_key=("id",),
        foreign_keys=("user_id -> users.id",),
        indexes=("ix_audit_logs_user_id",),
        create_sql="""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT NOT NULL AUTO_INCREMENT,
            action VARCHAR(120) NOT NULL,
            details TEXT NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            user_id INT NULL,
            created_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            KEY ix_audit_logs_user_id (user_id),
            CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        allowed_insert_columns=("action", "details", "ip_address", "user_id", "created_at"),
        allowed_update_columns=("action", "details", "ip_address", "user_id"),
    ),
    SchemaTable(
        name="notes",
        purpose="Stores private per-user notes linked optionally to topics.",
        columns=("id", "title", "body", "topic_id", "owner_id", "is_deleted", "created_at", "updated_at"),
        primary_key=("id",),
        foreign_keys=("owner_id -> users.id", "topic_id -> topics.id"),
        indexes=("ix_notes_owner_id", "ix_notes_topic_id"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS notes (
            id INT NOT NULL AUTO_INCREMENT,
            title VARCHAR(200) NOT NULL,
            body TEXT NOT NULL,
            topic_id INT NULL,
            owner_id INT NOT NULL,
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            KEY ix_notes_owner_id (owner_id),
            KEY ix_notes_topic_id (topic_id),
            CONSTRAINT fk_notes_owner FOREIGN KEY (owner_id) REFERENCES users(id),
            CONSTRAINT fk_notes_topic FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
        """,
        allowed_insert_columns=("title", "body", "topic_id", "owner_id", "is_deleted", "created_at", "updated_at"),
        allowed_update_columns=("title", "body", "topic_id", "is_deleted", "updated_at"),
    ),
    SchemaTable(
        name="note_access_requests",
        purpose="Tracks admin requests and user decisions before admins may view specific private notes.",
        columns=("id", "topic_id", "note_id", "requester_admin_id", "status", "requested_at", "responded_at"),
        primary_key=("id",),
        foreign_keys=("requester_admin_id -> users.id", "topic_id -> topics.id", "note_id -> notes.id"),
        indexes=("ix_note_access_admin_id", "ix_note_access_topic_id", "ix_note_access_note_id"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS note_access_requests (
            id INT NOT NULL AUTO_INCREMENT,
            topic_id INT NOT NULL,
            note_id INT NULL,
            requester_admin_id INT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            requested_at DATETIME NOT NULL,
            responded_at DATETIME NULL,
            PRIMARY KEY (id),
            KEY ix_note_access_admin_id (requester_admin_id),
            KEY ix_note_access_topic_id (topic_id),
            KEY ix_note_access_note_id (note_id),
            CONSTRAINT fk_note_access_admin FOREIGN KEY (requester_admin_id) REFERENCES users(id),
            CONSTRAINT fk_note_access_topic FOREIGN KEY (topic_id) REFERENCES topics(id),
            CONSTRAINT fk_note_access_note FOREIGN KEY (note_id) REFERENCES notes(id)
        )
        """,
        allowed_insert_columns=("topic_id", "note_id", "requester_admin_id", "status", "requested_at", "responded_at"),
        allowed_update_columns=("note_id", "status", "responded_at"),
    ),
    SchemaTable(
        name="lab_references",
        purpose="Stores user and admin lab references, topic links, visibility, and soft-delete state.",
        columns=(
            "id",
            "name",
            "platform_id",
            "url",
            "notes",
            "topic_id",
            "owner_id",
            "visibility",
            "is_deleted",
            "created_at",
            "updated_at",
        ),
        primary_key=("id",),
        foreign_keys=("owner_id -> users.id", "topic_id -> topics.id", "platform_id -> lab_platforms.id"),
        indexes=("ix_lab_references_owner_id", "ix_lab_references_topic_id", "ix_lab_references_platform_id"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS lab_references (
            id INT NOT NULL AUTO_INCREMENT,
            name VARCHAR(200) NOT NULL,
            platform_id INT NOT NULL,
            url VARCHAR(255) NOT NULL,
            notes TEXT NOT NULL,
            topic_id INT NULL,
            owner_id INT NOT NULL,
            visibility VARCHAR(20) NOT NULL DEFAULT 'personal',
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            KEY ix_lab_references_owner_id (owner_id),
            KEY ix_lab_references_topic_id (topic_id),
            KEY ix_lab_references_platform_id (platform_id),
            CONSTRAINT fk_lab_references_owner FOREIGN KEY (owner_id) REFERENCES users(id),
            CONSTRAINT fk_lab_references_topic FOREIGN KEY (topic_id) REFERENCES topics(id),
            CONSTRAINT fk_lab_references_platform FOREIGN KEY (platform_id) REFERENCES lab_platforms(id)
        )
        """,
        allowed_insert_columns=(
            "name",
            "platform_id",
            "url",
            "notes",
            "topic_id",
            "owner_id",
            "visibility",
            "is_deleted",
            "created_at",
            "updated_at",
        ),
        allowed_update_columns=("name", "platform_id", "url", "notes", "topic_id", "visibility", "is_deleted", "updated_at"),
    ),
    SchemaTable(
        name="lab_completions",
        purpose="Records which users completed which labs and when, one row per user/lab pair.",
        columns=("id", "lab_id", "user_id", "completed_at"),
        primary_key=("id",),
        foreign_keys=("lab_id -> lab_references.id", "user_id -> users.id"),
        indexes=("uq_lab_completion_user", "ix_lab_completions_user_id"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS lab_completions (
            id INT NOT NULL AUTO_INCREMENT,
            lab_id INT NOT NULL,
            user_id INT NOT NULL,
            completed_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_lab_completion_user (lab_id, user_id),
            KEY ix_lab_completions_user_id (user_id),
            CONSTRAINT fk_lab_completions_lab FOREIGN KEY (lab_id) REFERENCES lab_references(id),
            CONSTRAINT fk_lab_completions_user FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """,
        allowed_insert_columns=("lab_id", "user_id", "completed_at"),
        allowed_update_columns=("completed_at",),
    ),
    SchemaTable(
        name="scheduled_tasks",
        purpose="Stores personal and admin-assigned scheduled work with due dates, scope, and completion status.",
        columns=(
            "id",
            "user_id",
            "created_by",
            "title",
            "description",
            "task_type",
            "due_at",
            "status",
            "scope",
            "created_at",
            "updated_at",
        ),
        primary_key=("id",),
        foreign_keys=("user_id -> users.id", "created_by -> users.id"),
        indexes=("ix_scheduled_tasks_user_id", "ix_scheduled_tasks_created_by", "ix_scheduled_tasks_scope_status"),
        create_sql="""
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INT NOT NULL AUTO_INCREMENT,
            user_id INT NULL,
            created_by INT NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT NULL,
            task_type VARCHAR(40) NOT NULL DEFAULT 'general',
            due_at DATETIME NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'upcoming',
            scope VARCHAR(20) NOT NULL DEFAULT 'personal',
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            KEY ix_scheduled_tasks_user_id (user_id),
            KEY ix_scheduled_tasks_created_by (created_by),
            KEY ix_scheduled_tasks_scope_status (scope, status),
            CONSTRAINT fk_scheduled_tasks_user FOREIGN KEY (user_id) REFERENCES users(id),
            CONSTRAINT fk_scheduled_tasks_created_by FOREIGN KEY (created_by) REFERENCES users(id)
        )
        """,
        allowed_insert_columns=(
            "user_id",
            "created_by",
            "title",
            "description",
            "task_type",
            "due_at",
            "status",
            "scope",
            "created_at",
            "updated_at",
        ),
        allowed_update_columns=("user_id", "title", "description", "task_type", "due_at", "status", "scope", "updated_at"),
    ),
)


TABLE_REGISTRY = {table.name: table for table in TABLES}

COLUMN_ALTERS = {
    "users": {
        "display_name": "ALTER TABLE users ADD COLUMN display_name VARCHAR(120) NOT NULL DEFAULT ''",
        "role": "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'",
        "is_banned": "ALTER TABLE users ADD COLUMN is_banned BOOLEAN NOT NULL DEFAULT FALSE",
        "mfa_secret": "ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(64) NULL",
        "mfa_enabled": "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE",
        "auth_version": "ALTER TABLE users ADD COLUMN auth_version INT NOT NULL DEFAULT 0",
        "failed_login_count": "ALTER TABLE users ADD COLUMN failed_login_count INT NOT NULL DEFAULT 0",
        "last_failed_login_at": "ALTER TABLE users ADD COLUMN last_failed_login_at DATETIME NULL",
        "locked_until": "ALTER TABLE users ADD COLUMN locked_until DATETIME NULL",
        "profile_bio": "ALTER TABLE users ADD COLUMN profile_bio TEXT NULL",
        "profile_image": "ALTER TABLE users ADD COLUMN profile_image CHAR(64) NULL",
        "updated_at": "ALTER TABLE users ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    },
    "categories": {
        "is_deleted": "ALTER TABLE categories ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE",
    },
    "topics": {
        "slug": "ALTER TABLE topics ADD COLUMN slug VARCHAR(220) NOT NULL DEFAULT '' AFTER title",
        "is_deleted": "ALTER TABLE topics ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE",
    },
    "notes": {
        "is_deleted": "ALTER TABLE notes ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE",
    },
    "lab_references": {
        "visibility": "ALTER TABLE lab_references ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'personal'",
        "is_deleted": "ALTER TABLE lab_references ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE",
    },
    "scheduled_tasks": {
        "description": "ALTER TABLE scheduled_tasks ADD COLUMN description TEXT NULL",
        "task_type": "ALTER TABLE scheduled_tasks ADD COLUMN task_type VARCHAR(40) NOT NULL DEFAULT 'general'",
        "scope": "ALTER TABLE scheduled_tasks ADD COLUMN scope VARCHAR(20) NOT NULL DEFAULT 'personal'",
    },
}

USER_COLUMN_ALTERS = COLUMN_ALTERS["users"]
TABLE_COLUMN_ALTERS = {name: alters for name, alters in COLUMN_ALTERS.items() if name != "users"}

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KNOWN_IDENTIFIERS = set(TABLE_REGISTRY)
for _table in TABLES:
    _KNOWN_IDENTIFIERS.update(_table.columns)


def get_table(name: str) -> SchemaTable:
    try:
        return TABLE_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown schema table: {name}") from exc


def get_create_statements() -> list[str]:
    return [table.create_sql for table in TABLES]


def get_column_alters(table_name: str | None = None) -> dict[str, str] | dict[str, dict[str, str]]:
    if table_name is None:
        return {name: dict(alters) for name, alters in COLUMN_ALTERS.items()}
    if table_name not in COLUMN_ALTERS:
        raise ValueError(f"Unknown schema table with compatibility alters: {table_name}")
    return dict(COLUMN_ALTERS[table_name])


def quote_identifier(name: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(name) or name not in _KNOWN_IDENTIFIERS:
        raise ValueError(f"Unsafe or unknown SQL identifier: {name}")
    return f"`{name}`"


def build_insert_sql(table_name: str, columns: Sequence[str]) -> str:
    table = get_table(table_name)
    selected_columns = _validate_columns(table, columns, table.allowed_insert_columns, "insert")
    column_sql = ", ".join(quote_identifier(column) for column in selected_columns)
    placeholders = ", ".join(["%s"] * len(selected_columns))
    return f"INSERT INTO {quote_identifier(table.name)} ({column_sql}) VALUES ({placeholders})"


def build_update_sql(table_name: str, columns: Sequence[str], where_clause: str) -> str:
    table = get_table(table_name)
    selected_columns = _validate_columns(table, columns, table.allowed_update_columns, "update")
    safe_where = where_clause.strip()
    if not safe_where or ";" in safe_where:
        raise ValueError("where_clause must be a trusted static SQL fragment without semicolons")
    if not safe_where.lower().startswith("where "):
        safe_where = f"WHERE {safe_where}"
    assignments = ", ".join(f"{quote_identifier(column)} = %s" for column in selected_columns)
    return f"UPDATE {quote_identifier(table.name)} SET {assignments} {safe_where}"


def _validate_columns(
    table: SchemaTable,
    columns: Sequence[str],
    allowed_columns: tuple[str, ...],
    operation: str,
) -> tuple[str, ...]:
    selected_columns = tuple(columns)
    if not selected_columns:
        raise ValueError(f"At least one column is required to build an {operation} statement")
    if len(set(selected_columns)) != len(selected_columns):
        raise ValueError(f"Duplicate columns are not allowed in {operation} statements")

    allowed = set(allowed_columns)
    for column in selected_columns:
        if column not in allowed:
            raise ValueError(f"Column {column} is not allowed for {operation} on {table.name}")
        quote_identifier(column)
    return selected_columns
