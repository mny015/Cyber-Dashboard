"""Perform a read-only database connectivity check through the pooled layer."""

import sys

from app import create_app
from app.utils.database import DatabaseError, connection


def check_database():
    with connection() as raw_connection:
        with raw_connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS healthy")
            row = cursor.fetchone()
    return bool(row and row["healthy"] == 1)


def main():
    application = create_app()
    try:
        with application.app_context():
            healthy = check_database()
    except (DatabaseError, RuntimeError) as exc:
        print(f"[FAIL] Database connection failed: {exc}", file=sys.stderr)
        return 1

    print("Database connection is healthy." if healthy else "Database check failed.")
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
