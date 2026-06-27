from sqlalchemy import text
import pymysql

from app import create_app
from app.models import db


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


def add_column_if_missing(cursor, table_name, column_name, column_sql):
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
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


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

            add_column_if_missing(cursor, "users", "display_name", "display_name VARCHAR(120) NOT NULL DEFAULT ''")
            add_column_if_missing(cursor, "users", "role", "role VARCHAR(20) NOT NULL DEFAULT 'user'")
            add_column_if_missing(cursor, "users", "is_banned", "is_banned BOOLEAN NOT NULL DEFAULT FALSE")
            add_column_if_missing(cursor, "users", "mfa_secret", "mfa_secret VARCHAR(64) NULL")
            add_column_if_missing(cursor, "users", "mfa_enabled", "mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE")
            add_column_if_missing(cursor, "users", "updated_at", "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
    finally:
        connection.close()


def create_tables():
    app = create_app()
    with app.app_context():
        db.create_all()
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        print("Database connected and tables are ready.")


if __name__ == "__main__":
    ensure_database_exists()
    ensure_existing_user_columns()
    create_tables()
