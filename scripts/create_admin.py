"""Create or update an administrator after SQL migrations have been applied."""

import sys
from getpass import getpass

from app import create_app
from app.models import User
from app.repositories import user_repository
from app.utils.database import DatabaseError, db, transaction
from app.utils.validation import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    is_valid_email,
    normalize_email,
)


def create_or_update_admin(email, display_name, password):
    normalized_email = normalize_email(email)
    if not is_valid_email(normalized_email):
        raise ValueError("Enter a valid email address.")
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Password must contain between {PASSWORD_MIN_LENGTH} and "
            f"{PASSWORD_MAX_LENGTH} characters."
        )

    existing = user_repository.find_by_email(normalized_email)
    if existing:
        existing.set_password(password)
        with transaction() as cursor:
            database = db.using(cursor)
            database.table(User.TABLE_NAME).where("id", "=", existing.id).update(
                {
                    "display_name": display_name,
                    "password_hash": existing.password_hash,
                    "role": "admin",
                    "is_banned": False,
                    "auth_version": existing.auth_version + 1,
                    "failed_login_count": 0,
                    "last_failed_login_at": None,
                    "locked_until": None,
                }
            )
        return "updated"

    admin = User(
        email=normalized_email,
        display_name=display_name,
        role="admin",
    )
    admin.set_password(password)
    with transaction() as cursor:
        user_repository.create(admin, database=db.using(cursor))
    return "created"


def main():
    application = create_app()
    email = input("Admin email: ")
    display_name = input("Admin display name: ").strip() or "Admin"
    password = getpass("Password: ")

    try:
        with application.app_context():
            outcome = create_or_update_admin(email, display_name, password)
    except (DatabaseError, RuntimeError, ValueError) as exc:
        print(f"[FAIL] Administrator was not created: {exc}", file=sys.stderr)
        return 1

    print(f"Administrator {outcome} successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
