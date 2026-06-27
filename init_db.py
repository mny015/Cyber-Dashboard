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


USER_COLUMN_ALTERS = {
    "display_name": "ALTER TABLE users ADD COLUMN display_name VARCHAR(120) NOT NULL DEFAULT ''",
    "role": "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'",
    "is_banned": "ALTER TABLE users ADD COLUMN is_banned BOOLEAN NOT NULL DEFAULT FALSE",
    "mfa_secret": "ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(64) NULL",
    "mfa_enabled": "ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE",
    "updated_at": "ALTER TABLE users ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
}


def add_user_column_if_missing(cursor, column_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'users'
          AND COLUMN_NAME = %s
        """,
        (column_name,),
    )
    exists = cursor.fetchone()[0] > 0
    if not exists:
        cursor.execute(USER_COLUMN_ALTERS[column_name])


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
