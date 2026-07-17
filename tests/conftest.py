import os
import time
import uuid

import pytest
from werkzeug.security import generate_password_hash

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-use-env-file-for-real-app")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_USER", "cyber_dashboard_test")
os.environ.setdefault("DB_PASSWORD", "replace-with-test-password")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "").strip()
os.environ["DB_NAME"] = TEST_DB_NAME or "cyber_dashboard_test_unconfigured"
os.environ.setdefault("DB_CHARSET", "utf8mb4")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")

from app import create_app
from tests.support.database import TestDatabase

SYSTEM_DATABASES = {"information_schema", "mysql", "performance_schema", "sys"}


@pytest.fixture(scope="session")
def dedicated_test_database():
    if not TEST_DB_NAME:
        pytest.skip("Set TEST_DB_NAME to run tests that access MySQL.")

    normalized_name = TEST_DB_NAME.lower()
    if "test" not in normalized_name or normalized_name in SYSTEM_DATABASES:
        pytest.fail("TEST_DB_NAME must identify a dedicated test database and contain 'test'.")

    return TEST_DB_NAME


@pytest.fixture(scope="session")
def app():
    test_app = create_app()
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
    )
    return test_app


@pytest.fixture(scope="session")
def database(app, dedicated_test_database):
    test_database = TestDatabase(app, dedicated_test_database)
    test_database.assert_connected_to_test_database()
    return test_database


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user_factory(database):
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
        _, user_id = database.execute(
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

        user = database.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
        user["plain_password"] = password
        return user

    yield create_user

    for user_id in reversed(created_user_ids):
        cleanup_user_records(database, user_id)


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
            session["reauthenticated_at"] = int(time.time())
            session["reauthenticated_auth_version"] = int(user.get("auth_version") or 0)

    return authenticate


@pytest.fixture()
def authenticated_client(client, test_user, login_as):
    login_as(client, test_user)
    return client


@pytest.fixture()
def admin_client(client, admin_user, login_as):
    login_as(client, admin_user)
    return client


def cleanup_user_records(database, user_id):
    database.execute(
        "DELETE FROM scheduled_tasks WHERE user_id = %s OR created_by = %s",
        (user_id, user_id),
    )
    database.execute("DELETE FROM audit_logs WHERE user_id = %s", (user_id,))
    database.execute("DELETE FROM security_findings WHERE owner_id = %s", (user_id,))
    database.execute(
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
    database.execute(
        """
        DELETE FROM vulnerability_catalog
        WHERE created_by_user_id = %s OR reviewed_by_user_id = %s
        """,
        (user_id, user_id),
    )
    database.execute(
        """
        DELETE FROM note_access_requests
        WHERE requester_admin_id = %s
           OR topic_id IN (SELECT id FROM topics WHERE owner_id = %s)
        """,
        (user_id, user_id),
    )
    database.execute(
        """
        DELETE FROM lab_completions
        WHERE user_id = %s
           OR lab_id IN (SELECT id FROM lab_references WHERE owner_id = %s)
        """,
        (user_id, user_id),
    )
    database.execute("DELETE FROM notes WHERE owner_id = %s", (user_id,))
    database.execute("DELETE FROM lab_references WHERE owner_id = %s", (user_id,))
    database.execute("DELETE FROM topics WHERE owner_id = %s", (user_id,))
    database.execute("DELETE FROM contacts WHERE owner_id = %s", (user_id,))
    database.execute("DELETE FROM categories WHERE owner_id = %s", (user_id,))
    database.execute("DELETE FROM users WHERE id = %s", (user_id,))
