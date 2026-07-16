from pathlib import Path


def test_theme_toggle_present_on_login_page(client):
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert b"data-theme-toggle" in response.data
    assert b"theme-icon" in response.data
    assert b"data-theme-label" not in response.data
    assert b'id="favicon"' in response.data
    assert b"image/Favicon.png" in response.data
    assert b"image/logo-dark.png" in response.data
    assert b"auth-logo" in response.data


def test_theme_script_exists():
    assert Path("app/static/js/theme.js").exists()
    assert Path("app/static/image/logo-dark.png").exists()
    assert Path("app/static/image/Favicon.png").exists()


def test_theme_palette_uses_requested_dark_background_colors():
    stylesheet = Path("app/static/css/main.css").read_text(encoding="utf-8")

    assert "--background: #4d524e;" in stylesheet
    assert "--background: #1d1f1e;" in stylesheet
    assert "--surface: #3d423e;" in stylesheet
    assert "--surface: #262a27;" in stylesheet
    assert "--dashboard-accent: var(--accent);" in stylesheet


def test_shared_layout_has_no_developer_contact_footer(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Contact Developer" not in response.data
    assert b'Developer contact' not in response.data


def test_lab_and_task_actions_use_aligned_layout_hooks():
    labs_template = Path("app/templates/labs/index.html").read_text(encoding="utf-8")
    tasks_template = Path("app/templates/tasks/index.html").read_text(encoding="utf-8")
    stylesheet = Path("app/static/css/main.css").read_text(encoding="utf-8")

    assert 'class="card lab-card"' in labs_template
    assert 'class="actions lab-card-actions"' in labs_template
    assert ".lab-card-actions" in stylesheet
    assert "margin-top: auto !important;" in stylesheet
    assert 'class="actions task-item-actions"' in tasks_template
    assert ".task-item-actions" in stylesheet
    assert "grid-template-columns: 64px minmax(0, 1fr);" in stylesheet


def test_admin_user_avatar_uses_image_or_centered_text_fallback():
    template = Path("app/templates/admin/users.html").read_text(encoding="utf-8")
    stylesheet = Path("app/static/css/main.css").read_text(encoding="utf-8")

    assert "{% if user.profile_image %}" in template
    assert "profile.picture" in template
    assert "user-avatar-image" in template
    assert "user-avatar-fallback" in template
    assert ".user-identity-copy span" in stylesheet
    assert ".user-identity span" not in stylesheet
    assert "line-height: 1;" in stylesheet
    assert "text-align: center;" in stylesheet


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
    assert b"Note access requests" in response.data


def test_audit_logs_rejects_normal_user(authenticated_client):
    user_response = authenticated_client.get("/admin/audit-logs")

    assert user_response.status_code == 403


def test_audit_logs_loads_for_admin(admin_client):
    admin_response = admin_client.get("/admin/audit-logs")

    assert admin_response.status_code == 200


def test_profile_page_loads_with_professional_sections(authenticated_client):
    response = authenticated_client.get("/profile/")

    assert response.status_code == 200
    assert b"Account details" in response.data
    assert b"Privacy and security" in response.data


def test_profile_sections_share_the_available_column_width():
    stylesheet = Path("app/static/css/main.css").read_text(encoding="utf-8")
    profile_form_rule = stylesheet.rsplit(".profile-form-card {", 1)[1].split("}", 1)[0]
    security_panel_rule = stylesheet.rsplit(".profile-security-panel {", 1)[1].split("}", 1)[0]

    assert "width: 100%;" in profile_form_rule
    assert "width: 100%;" in security_panel_rule
