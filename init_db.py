import hashlib
import os

import pymysql

from app import create_app
from utils.db import get_connection


IMAGE_MIME_BY_TYPE = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def ensure_database_exists():
    connection = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="root",
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS cyber_dashboard "
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
    "profile_bio": "ALTER TABLE users ADD COLUMN profile_bio TEXT NULL",
    "profile_image": "ALTER TABLE users ADD COLUMN profile_image VARCHAR(255) NULL",
    "profile_image_data": "ALTER TABLE users ADD COLUMN profile_image_data LONGBLOB NULL",
    "profile_image_mime": "ALTER TABLE users ADD COLUMN profile_image_mime VARCHAR(80) NULL",
    "profile_image_size": "ALTER TABLE users ADD COLUMN profile_image_size INT NOT NULL DEFAULT 0",
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
}

DDL_STATEMENTS = [
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
        profile_bio TEXT NULL,
        profile_image VARCHAR(255) NULL,
        profile_image_data LONGBLOB NULL,
        profile_image_mime VARCHAR(80) NULL,
        profile_image_size INT NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uq_users_email (email)
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
        owner_id INT NOT NULL,
        requester_admin_id INT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        requested_at DATETIME NOT NULL,
        responded_at DATETIME NULL,
        PRIMARY KEY (id),
        KEY ix_note_access_owner_id (owner_id),
        KEY ix_note_access_admin_id (requester_admin_id),
        KEY ix_note_access_topic_id (topic_id),
        KEY ix_note_access_note_id (note_id),
        CONSTRAINT fk_note_access_owner FOREIGN KEY (owner_id) REFERENCES users(id),
        CONSTRAINT fk_note_access_admin FOREIGN KEY (requester_admin_id) REFERENCES users(id),
        CONSTRAINT fk_note_access_topic FOREIGN KEY (topic_id) REFERENCES topics(id),
        CONSTRAINT fk_note_access_note FOREIGN KEY (note_id) REFERENCES notes(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lab_references (
        id INT NOT NULL AUTO_INCREMENT,
        name VARCHAR(200) NOT NULL,
        vendor VARCHAR(120) NOT NULL,
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
        CONSTRAINT fk_lab_references_owner FOREIGN KEY (owner_id) REFERENCES users(id),
        CONSTRAINT fk_lab_references_topic FOREIGN KEY (topic_id) REFERENCES topics(id)
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
    connection = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="root",
        database="cyber_dashboard",
        charset="utf8mb4",
        autocommit=True,
    )
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
    connection = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="root",
        database="cyber_dashboard",
        charset="utf8mb4",
        autocommit=True,
    )
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


def migrate_static_profile_images_to_db():
    app = create_app()
    with app.app_context():
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, profile_image
                    FROM users
                    WHERE profile_image IS NOT NULL
                      AND profile_image <> ''
                      AND profile_image_data IS NULL
                    """
                )
                users = cursor.fetchall()
                for user in users:
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
                        UPDATE users
                        SET profile_image = %s,
                            profile_image_data = %s,
                            profile_image_mime = %s,
                            profile_image_size = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (digest, image_bytes, IMAGE_MIME_BY_TYPE[image_type], len(image_bytes), user["id"]),
                    )
                    os.remove(disk_path)
            connection.commit()
        finally:
            connection.close()


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
    migrate_static_profile_images_to_db()
