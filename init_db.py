import pymysql

from app import create_app
from utils.db import fetch_one, get_connection


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


if __name__ == "__main__":
    ensure_database_exists()
    ensure_existing_user_columns()
    ensure_existing_learning_columns()
    create_tables()
