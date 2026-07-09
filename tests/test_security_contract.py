from uuid import uuid4

from app import create_app
from utils.db import execute


def test_anonymous_users_cannot_access_private_dashboards(client):
    for path in ("/dashboard", "/user/dashboard", "/admin/dashboard"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]


def test_normal_user_cannot_access_administrator_routes(authenticated_client):
    admin_paths = (
        "/admin/dashboard",
        "/admin/users",
        "/admin/topics",
        "/admin/categories",
        "/admin/note-requests",
        "/admin/note-requests/1/note",
        "/admin/audit-logs",
        "/security/admin/vulnerabilities",
        "/backup/admin.json",
        "/backup/admin.zip",
    )

    for path in admin_paths:
        assert authenticated_client.get(path).status_code == 403


def test_owner_scoped_records_are_hidden_from_other_users(client, user_factory, login_as):
    owner = user_factory(display_name="Contract Owner")
    viewer = user_factory(display_name="Contract Viewer")
    suffix = uuid4().hex[:10]

    _, category_id = execute(
        """
        INSERT INTO categories
            (name, description, color, is_deleted, owner_id, created_at, updated_at)
        VALUES (%s, '', '#1677ff', 0, %s, NOW(), NOW())
        """,
        (f"Contract Category {suffix}", owner["id"]),
    )
    _, topic_id = execute(
        """
        INSERT INTO topics
            (title, slug, description, status, priority, notes, is_deleted,
             category_id, owner_id, created_at, updated_at)
        VALUES (%s, %s, '', 'planned', 'medium', '', 0, %s, %s, NOW(), NOW())
        """,
        (f"Contract Topic {suffix}", f"contract-topic-{suffix}", category_id, owner["id"]),
    )
    _, contact_id = execute(
        """
        INSERT INTO contacts
            (name, email, phone, notes, is_deleted, owner_id, created_at, updated_at)
        VALUES (%s, %s, '+1 555 010 9090', '', 0, %s, NOW(), NOW())
        """,
        (f"Contract Contact {suffix}", f"contract-{suffix}@example.com", owner["id"]),
    )
    _, note_id = execute(
        """
        INSERT INTO notes
            (title, body, topic_id, owner_id, is_deleted, created_at, updated_at)
        VALUES (%s, 'Private contract body', %s, %s, 0, NOW(), NOW())
        """,
        (f"Contract Note {suffix}", topic_id, owner["id"]),
    )
    _, finding_id = execute(
        """
        INSERT INTO security_findings
            (owner_id, vulnerability_id, threat_id, activity_type, title,
             target, severity, status, evidence, notes, detected_at,
             is_deleted, created_at, updated_at)
        VALUES (%s, NULL, NULL, 'vulnerability_found', %s,
                '', 'medium', 'open', '', '', NOW(), 0, NOW(), NOW())
        """,
        (owner["id"], f"Contract Finding {suffix}"),
    )

    login_as(client, viewer)
    protected_paths = (
        f"/categories/{category_id}/edit",
        f"/topics/{topic_id}",
        f"/contacts/{contact_id}/edit",
        f"/notes/{note_id}",
        f"/security/{finding_id}/edit",
    )

    for path in protected_paths:
        assert client.get(path).status_code == 404


def test_logout_is_post_only(client):
    assert client.get("/auth/logout").status_code == 405


def test_production_csrf_protection_is_enabled():
    production_app = create_app()

    assert production_app.config["WTF_CSRF_ENABLED"] is True
    assert "csrf" in production_app.extensions

    response = production_app.test_client().post(
        "/auth/register",
        data={
            "display_name": "Missing CSRF",
            "email": "missing-csrf@example.com",
            "password": "MissingCsrfPassword123!",
            "confirm_password": "MissingCsrfPassword123!",
        },
    )
    assert response.status_code == 400
