from pathlib import Path


def test_theme_toggle_present_on_login_page(client):
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert b"data-theme-toggle" in response.data


def test_theme_script_exists():
    assert Path("app/static/js/theme.js").exists()


def test_topics_page_loads(authenticated_client):
    response = authenticated_client.get("/topics/")

    assert response.status_code == 200
    assert b"Topics" in response.data


def test_notes_page_loads(authenticated_client):
    response = authenticated_client.get("/notes/")

    assert response.status_code == 200
    assert b"Notes" in response.data


def test_labs_page_loads(authenticated_client):
    response = authenticated_client.get("/labs/")

    assert response.status_code == 200
    assert b"Labs" in response.data


def test_requests_page_loads_for_admin(admin_client):
    response = admin_client.get("/admin/note-requests")

    assert response.status_code == 200
    assert b"Note Requests" in response.data


def test_audit_logs_rejects_normal_user(authenticated_client):
    user_response = authenticated_client.get("/admin/audit-logs")

    assert user_response.status_code == 403


def test_audit_logs_loads_for_admin(admin_client):
    admin_response = admin_client.get("/admin/audit-logs")

    assert admin_response.status_code == 200
