import json
from uuid import uuid4

from utils.db import execute, fetch_one


def create_admin_public_lab(admin_id):
    platform = fetch_one("SELECT id FROM lab_platforms ORDER BY id LIMIT 1")
    name = f"Public lab {uuid4().hex[:8]}"
    _, lab_id = execute(
        """
        INSERT INTO lab_references
            (name, platform_id, url, notes, topic_id, owner_id, visibility,
             is_deleted, created_at, updated_at)
        VALUES (%s, %s, %s, '', NULL, %s, 'public', 0, NOW(), NOW())
        """,
        (name, platform["id"], f"https://example.com/{name}", admin_id),
    )
    return lab_id, name


def test_public_admin_lab_appears_on_user_dashboard(client, test_user, admin_user, login_as):
    _, lab_name = create_admin_public_lab(admin_user["id"])
    login_as(client, test_user)

    response = client.get("/user/dashboard")

    assert response.status_code == 200
    assert lab_name.encode() in response.data
    assert b"Shared" in response.data


def test_admin_backup_exports_public_labs(admin_client, admin_user):
    _, lab_name = create_admin_public_lab(admin_user["id"])

    response = admin_client.get("/backup/admin.json")
    payload = json.loads(response.get_data(as_text=True))

    assert response.status_code == 200
    assert any(
        lab["name"] == lab_name and lab["visibility"] == "public"
        for lab in payload["shared_labs"]
    )
