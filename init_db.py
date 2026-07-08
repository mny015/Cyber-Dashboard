import hashlib
import os
import re

import pymysql

from app import create_app
from config import Config
from utils.db import get_connection
from utils.security_catalog import APP_VULNERABILITIES, THREAT_TACTICS


IMAGE_MIME_BY_TYPE = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def database_identifier(name):
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise RuntimeError("DB_NAME may only contain letters, numbers, and underscores.")
    return f"`{name}`"


def bootstrap_connection(database=None):
    kwargs = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "charset": Config.DB_CHARSET,
        "autocommit": True,
    }
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def ensure_database_exists():
    connection = bootstrap_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {database_identifier(Config.DB_NAME)} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        connection.close()


USER_COLUMN_ALTERS = {
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
}

TABLE_COLUMN_ALTERS = {
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

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS profile_images (
        image_hash CHAR(64) NOT NULL,
        image_data LONGBLOB NOT NULL,
        mime_type VARCHAR(80) NOT NULL,
        byte_size INT NOT NULL,
        created_at DATETIME NOT NULL,
        PRIMARY KEY (image_hash)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lab_platforms (
        id INT NOT NULL AUTO_INCREMENT,
        name VARCHAR(120) NOT NULL,
        slug VARCHAR(120) NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uq_lab_platform_name (name),
        UNIQUE KEY uq_lab_platform_slug (slug)
    )
    """,
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
    """
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
]


def add_user_column_if_missing(cursor, column_name):
    add_column_if_missing(cursor, "users", column_name, USER_COLUMN_ALTERS[column_name])


def add_column_if_missing(cursor, table_name, column_name, alter_statement):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table_name, column_name),
    )
    exists = cursor.fetchone()[0] > 0
    if not exists:
        cursor.execute(alter_statement)


def ensure_existing_user_columns():
    connection = bootstrap_connection(Config.DB_NAME)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE %s", ("users",))
            if not cursor.fetchone():
                return

            for column_name in USER_COLUMN_ALTERS:
                add_user_column_if_missing(cursor, column_name)
    finally:
        connection.close()


def ensure_existing_learning_columns():
    connection = bootstrap_connection(Config.DB_NAME)
    try:
        with connection.cursor() as cursor:
            for table_name, columns in TABLE_COLUMN_ALTERS.items():
                cursor.execute("SHOW TABLES LIKE %s", (table_name,))
                if not cursor.fetchone():
                    continue
                for column_name, alter_statement in columns.items():
                    add_column_if_missing(cursor, table_name, column_name, alter_statement)
            cursor.execute("UPDATE topics SET slug = LOWER(REPLACE(title, ' ', '-')) WHERE slug = ''")
    finally:
        connection.close()


def create_tables():
    app = create_app()
    with app.app_context():
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                for statement in DDL_STATEMENTS:
                    cursor.execute(statement)
            connection.commit()
        finally:
            connection.close()
        print("Database connected and tables are ready.")


def seed_security_catalog():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
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
                    (
                        code,
                        name,
                        category,
                        severity,
                        f"Curated catalog entry from {source}.",
                        source,
                    ),
                )
            for code, name, level in THREAT_TACTICS:
                cursor.execute(
                    """
                    INSERT INTO threat_catalog
                        (code, name, default_level, description, source, is_active, created_at, updated_at)
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
        connection.commit()
    finally:
        connection.close()


def normalize_profile_images():
    app = create_app()
    with app.app_context():
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                has_blob_columns = column_exists(cursor, "users", "profile_image_data")
                if has_blob_columns:
                    cursor.execute(
                        """
                        SELECT id, profile_image, profile_image_data, profile_image_mime, profile_image_size
                        FROM users
                        WHERE profile_image_data IS NOT NULL
                        """
                    )
                    for user in cursor.fetchall():
                        image_bytes = user["profile_image_data"]
                        image_type = detect_image_type_from_bytes(image_bytes)
                        if image_type not in IMAGE_MIME_BY_TYPE:
                            continue
                        digest = hashlib.sha256(image_bytes).hexdigest()
                        cursor.execute(
                            """
                            INSERT INTO profile_images (image_hash, image_data, mime_type, byte_size, created_at)
                            VALUES (%s, %s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE image_hash = VALUES(image_hash)
                            """,
                            (digest, image_bytes, IMAGE_MIME_BY_TYPE[image_type], len(image_bytes)),
                        )
                        cursor.execute("UPDATE users SET profile_image = %s WHERE id = %s", (digest, user["id"]))

                cursor.execute(
                    "SELECT id, profile_image FROM users WHERE profile_image IS NOT NULL AND profile_image <> ''"
                )
                for user in cursor.fetchall():
                    old_path = user["profile_image"]
                    if not old_path.startswith("uploads/profiles/"):
                        continue
                    disk_path = os.path.join(app.root_path, "static", old_path)
                    if not os.path.exists(disk_path):
                        continue
                    with open(disk_path, "rb") as image_file:
                        image_bytes = image_file.read()
                    image_type = detect_image_type_from_bytes(image_bytes)
                    if image_type not in IMAGE_MIME_BY_TYPE:
                        continue
                    digest = hashlib.sha256(image_bytes).hexdigest()
                    cursor.execute(
                        """
                        INSERT INTO profile_images (image_hash, image_data, mime_type, byte_size, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        ON DUPLICATE KEY UPDATE image_hash = VALUES(image_hash)
                        """,
                        (digest, image_bytes, IMAGE_MIME_BY_TYPE[image_type], len(image_bytes)),
                    )
                    cursor.execute("UPDATE users SET profile_image = %s WHERE id = %s", (digest, user["id"]))
                    os.remove(disk_path)

                cursor.execute(
                    """
                    UPDATE users
                    SET profile_image = NULL
                    WHERE profile_image IS NOT NULL AND CHAR_LENGTH(profile_image) <> 64
                    """
                )
                cursor.execute("ALTER TABLE users MODIFY profile_image CHAR(64) NULL")

                profile_column_drops = {
                    "profile_image_data": "ALTER TABLE users DROP COLUMN profile_image_data",
                    "profile_image_mime": "ALTER TABLE users DROP COLUMN profile_image_mime",
                    "profile_image_size": "ALTER TABLE users DROP COLUMN profile_image_size",
                }
                for column_name, statement in profile_column_drops.items():
                    if column_exists(cursor, "users", column_name):
                        cursor.execute(statement)

                if not foreign_key_exists(cursor, "users", "profile_image"):
                    cursor.execute(
                        """
                        ALTER TABLE users
                        ADD CONSTRAINT fk_users_profile_image
                        FOREIGN KEY (profile_image) REFERENCES profile_images(image_hash)
                        """
                    )
            connection.commit()
        finally:
            connection.close()


def normalize_lab_platforms():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if column_exists(cursor, "lab_references", "visibility"):
                cursor.execute("UPDATE lab_references SET visibility = 'public' WHERE visibility = 'everyone'")

            for name in ("picoCTF", "TryHackMe", "Hack The Box", "PortSwigger", "Other"):
                cursor.execute(
                    "INSERT IGNORE INTO lab_platforms (name, slug) VALUES (%s, %s)",
                    (name, platform_slug(name)),
                )

            if not column_exists(cursor, "lab_references", "platform_id"):
                cursor.execute("ALTER TABLE lab_references ADD COLUMN platform_id INT NULL AFTER name")

            if column_exists(cursor, "lab_references", "vendor"):
                cursor.execute("SELECT DISTINCT vendor FROM lab_references WHERE vendor <> ''")
                for row in cursor.fetchall():
                    name = row["vendor"]
                    cursor.execute(
                        "INSERT IGNORE INTO lab_platforms (name, slug) VALUES (%s, %s)",
                        (name, platform_slug(name)),
                    )
                cursor.execute(
                    """
                    UPDATE lab_references AS labs
                    JOIN lab_platforms AS platforms ON platforms.name = labs.vendor
                    SET labs.platform_id = platforms.id
                    WHERE labs.platform_id IS NULL
                    """
                )

            cursor.execute(
                """
                UPDATE lab_references
                SET platform_id = (SELECT id FROM lab_platforms WHERE slug = 'other')
                WHERE platform_id IS NULL
                """
            )
            cursor.execute("ALTER TABLE lab_references MODIFY platform_id INT NOT NULL")

            if not foreign_key_exists(cursor, "lab_references", "platform_id"):
                cursor.execute(
                    """
                    ALTER TABLE lab_references
                    ADD CONSTRAINT fk_lab_references_platform
                    FOREIGN KEY (platform_id) REFERENCES lab_platforms(id)
                    """
                )
            if column_exists(cursor, "lab_references", "vendor"):
                cursor.execute("ALTER TABLE lab_references DROP COLUMN vendor")
        connection.commit()
    finally:
        connection.close()


def normalize_note_access_requests():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if not column_exists(cursor, "note_access_requests", "owner_id"):
                return
            if constraint_exists(cursor, "note_access_requests", "fk_note_access_owner"):
                cursor.execute("ALTER TABLE note_access_requests DROP FOREIGN KEY fk_note_access_owner")
            cursor.execute("ALTER TABLE note_access_requests DROP COLUMN owner_id")
        connection.commit()
    finally:
        connection.close()


def column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (table_name, column_name),
    )
    return cursor.fetchone()["total"] > 0


def foreign_key_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """,
        (table_name, column_name),
    )
    return cursor.fetchone()["total"] > 0


def constraint_exists(cursor, table_name, constraint_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND CONSTRAINT_NAME = %s
        """,
        (table_name, constraint_name),
    )
    return cursor.fetchone()["total"] > 0


def platform_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def detect_image_type_from_bytes(file_bytes):
    header = file_bytes[:512]
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"
    return None


if __name__ == "__main__":
    ensure_database_exists()
    ensure_existing_user_columns()
    ensure_existing_learning_columns()
    create_tables()
    seed_security_catalog()
    normalize_profile_images()
    normalize_lab_platforms()
    normalize_note_access_requests()
