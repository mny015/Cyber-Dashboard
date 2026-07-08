import hashlib
import os
import re

import pymysql

from app import create_app
from config import Config
from utils.db import get_connection
from utils.schema import get_column_alters, get_create_statements
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


USER_COLUMN_ALTERS = get_column_alters("users")
TABLE_COLUMN_ALTERS = {name: alters for name, alters in get_column_alters().items() if name != "users"}


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
            cursor.execute("SHOW TABLES LIKE %s", ("topics",))
            if cursor.fetchone():
                cursor.execute("UPDATE topics SET slug = LOWER(REPLACE(title, ' ', '-')) WHERE slug = ''")
    finally:
        connection.close()


def create_tables():
    app = create_app()
    with app.app_context():
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                for statement in get_create_statements():
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
