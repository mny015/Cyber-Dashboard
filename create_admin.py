from getpass import getpass

from app import create_app
from app.models.user import User
from init_db import create_tables, ensure_database_exists, ensure_existing_user_columns
from utils.db import execute, fetch_one
from utils.helpers import is_valid_email

app = create_app()


def run():
    ensure_database_exists()
    ensure_existing_user_columns()
    create_tables()

    with app.app_context():
        email = input("Admin email: ").strip().lower()
        if not is_valid_email(email):
            print("Enter a valid email address.")
            return

        display_name = input("Admin display name: ").strip() or "Admin"
        password = getpass("Password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            return

        existing = User.from_row(fetch_one("SELECT * FROM users WHERE email = %s", (email,)))
        if existing:
            print("User exists; updating role, password, and status.")
            existing.set_password(password)
            existing.role = "admin"
            existing.is_banned = False
            existing.display_name = display_name
            execute(
                """
                UPDATE users
                SET password_hash = %s, role = 'admin', is_banned = 0, display_name = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (existing.password_hash, existing.display_name, existing.id),
            )
        else:
            admin = User(display_name=display_name, email=email, role="admin")
            admin.set_password(password)
            execute(
                """
                INSERT INTO users (email, password_hash, display_name, role, is_banned, mfa_secret, mfa_enabled, created_at, updated_at)
                VALUES (%s, %s, %s, 'admin', 0, NULL, 0, NOW(), NOW())
                """,
                (admin.email, admin.password_hash, admin.display_name),
            )

        print("Admin user created/updated.")


if __name__ == "__main__":
    run()
