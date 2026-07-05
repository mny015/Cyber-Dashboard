import os
import uuid

import pytest
from werkzeug.security import generate_password_hash

os.environ.setdefault("SECRET_KEY", "test-secret-key-use-env-file-for-real-app")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_USER", "cyber_dashboard_test")
os.environ.setdefault("DB_PASSWORD", "replace-with-test-password")
os.environ.setdefault("DB_NAME", "cyber_dashboard")
os.environ.setdefault("DB_CHARSET", "utf8mb4")

from app import create_app
from utils.db import execute, fetch_one


@pytest.fixture(scope="session")
def app():
    test_app = create_app()
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
    )
    return test_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def user_factory():
    created_user_ids = []

    def create_user(
        email=None,
        password="TestPassword123!",
        display_name="Test User",
        role="user",
        is_banned=False,
        mfa_enabled=False,
    ):
        email = email or f"{role}-{uuid.uuid4().hex}@example.com"
        _, user_id = execute(
            """
            INSERT INTO users
                (email, password_hash, display_name, role, is_banned,
                 mfa_enabled, auth_version, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 0, NOW(), NOW())
            """,
            (
                email,
                generate_password_hash(password),
                display_name,
                role,
                int(is_banned),
                int(mfa_enabled),
            ),
        )
        created_user_ids.append(user_id)

        user = fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
        user["plain_password"] = password
        return user

    yield create_user

    for user_id in reversed(created_user_ids):
        cleanup_user_records(user_id)


@pytest.fixture()
def test_user(user_factory):
    return user_factory()


@pytest.fixture()
def admin_user(user_factory):
    return user_factory(role="admin", display_name="Admin User")


@pytest.fixture()
def login_as():
    def authenticate(client, user):
        with client.session_transaction() as session:
            session["_user_id"] = str(user["id"])
            session["_fresh"] = True
            session["auth_version"] = int(user.get("auth_version") or 0)

    return authenticate


@pytest.fixture()
def authenticated_client(client, test_user, login_as):
    login_as(client, test_user)
    return client


@pytest.fixture()
def admin_client(client, admin_user, login_as):
    login_as(client, admin_user)
    return client


def cleanup_user_records(user_id):
    execute("DELETE FROM scheduled_tasks WHERE user_id = %s OR created_by = %s", (user_id, user_id))
    execute("DELETE FROM audit_logs WHERE user_id = %s", (user_id,))
    execute("DELETE FROM security_findings WHERE owner_id = %s", (user_id,))
    execute(
        """
        DELETE FROM security_findings
        WHERE vulnerability_id IN (
            SELECT id
            FROM vulnerability_catalog
            WHERE created_by_user_id = %s OR reviewed_by_user_id = %s
        )
        """,
        (user_id, user_id),
    )
    execute(
        """
        DELETE FROM vulnerability_catalog
        WHERE created_by_user_id = %s OR reviewed_by_user_id = %s
        """,
        (user_id, user_id),
    )
    execute(
        """
        DELETE FROM note_access_requests
        WHERE requester_admin_id = %s
           OR topic_id IN (SELECT id FROM topics WHERE owner_id = %s)
           OR note_id IN (SELECT id FROM notes WHERE owner_id = %s)
        """,
        (user_id, user_id, user_id),
    )
    execute(
        """
        DELETE FROM lab_completions
        WHERE user_id = %s
           OR lab_id IN (SELECT id FROM lab_references WHERE owner_id = %s)
        """,
        (user_id, user_id),
    )
    execute("DELETE FROM notes WHERE owner_id = %s", (user_id,))
    execute("DELETE FROM lab_references WHERE owner_id = %s", (user_id,))
    execute("DELETE FROM topics WHERE owner_id = %s", (user_id,))
    execute("DELETE FROM contacts WHERE owner_id = %s", (user_id,))
    execute("DELETE FROM categories WHERE owner_id = %s", (user_id,))
    execute("DELETE FROM users WHERE id = %s", (user_id,))
