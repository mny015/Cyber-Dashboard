"""HTTP safety contracts for every state-changing workflow."""

import re
from pathlib import Path

import pytest
from flask import Flask
from flask_wtf.csrf import generate_csrf

from app.extensions import csrf, login_manager
from app.models import User
from app.routes import register_blueprints


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORM_PAGE_ENDPOINTS = {
    "admin.update_role",
    "admin.reset_user_password",
    "auth.register",
    "auth.login",
    "auth.verify_mfa",
    "auth.setup_mfa",
    "categories.create",
    "categories.edit",
    "contacts.create",
    "contacts.edit",
    "labs.create",
    "labs.edit",
    "notes.create",
    "notes.edit",
    "profile.edit",
    "security.admin_vulnerabilities",
    "security.create",
    "security.edit",
    "tasks.index",
    "topics.create",
    "topics.edit",
}

ACTION_ONLY_ENDPOINTS = {
    "admin.ban_user",
    "admin.delete_user",
    "admin.request_topic_notes",
    "admin.unban_user",
    "auth.change_password",
    "auth.logout",
    "backup.admin_csv",
    "backup.admin_json",
    "backup.personal_csv",
    "backup.personal_json",
    "categories.delete",
    "contacts.delete",
    "labs.complete",
    "labs.delete",
    "labs.incomplete",
    "notes.delete",
    "notifications.approve",
    "notifications.deny",
    "security.approve_vulnerability",
    "security.delete",
    "security.reject_vulnerability",
    "security.suggest_vulnerability",
    "tasks.cancel",
    "tasks.complete",
    "topics.delete",
}


@pytest.fixture()
def action_app():
    app = Flask(
        __name__, template_folder=str(PROJECT_ROOT / "app" / "templates")
    )
    app.config.update(
        SECRET_KEY="state-change-contract-secret",
        TESTING=True,
        WTF_CSRF_ENABLED=True,
        RATELIMIT_ENABLED=False,
    )
    original_login_view = login_manager.login_view
    original_user_callback = login_manager._user_callback
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "test_login"

    @login_manager.user_loader
    def load_user(user_id):
        return User(
            id=int(user_id),
            email="student@example.com",
            display_name="Student",
            role="user",
        )

    @app.get("/test-login")
    def test_login():
        return "login"

    @app.get("/test-csrf")
    def test_csrf():
        return generate_csrf()

    register_blueprints(app)
    yield app

    login_manager.login_view = original_login_view
    login_manager._user_callback = original_user_callback


@pytest.fixture()
def action_client(action_app):
    client = action_app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "7"
        session["_fresh"] = True
        session["auth_version"] = 0
    return client


def csrf_token(client):
    return client.get("/test-csrf").get_data(as_text=True)


def test_every_state_changing_endpoint_accepts_post(action_app):
    methods_by_endpoint = {
        rule.endpoint: rule.methods
        for rule in action_app.url_map.iter_rules()
        if rule.endpoint not in {"static", "test_login", "test_csrf"}
    }

    for endpoint in FORM_PAGE_ENDPOINTS | ACTION_ONLY_ENDPOINTS:
        assert "POST" in methods_by_endpoint[endpoint], endpoint


def test_action_only_endpoints_reject_get_without_calling_controller(action_app):
    methods_by_endpoint = {
        rule.endpoint: rule.methods for rule in action_app.url_map.iter_rules()
    }

    for endpoint in ACTION_ONLY_ENDPOINTS:
        assert "GET" not in methods_by_endpoint[endpoint], endpoint


def test_get_form_display_does_not_create_category(monkeypatch, action_client):
    writes = []
    monkeypatch.setattr(
        "app.controllers.categories_controller.category_repository.create",
        lambda category: writes.append(category),
    )

    response = action_client.get("/categories/new")

    assert response.status_code == 200
    assert writes == []


def test_get_mfa_page_does_not_create_secret(monkeypatch, action_client):
    writes = []
    monkeypatch.setattr(
        "app.controllers.auth_controller.auth_service.ensure_mfa_secret",
        lambda user: writes.append(user),
    )

    response = action_client.get("/auth/profile/mfa")

    assert response.status_code == 200
    assert writes == []


def test_missing_csrf_rejects_action_before_mutation(monkeypatch, action_client):
    writes = []
    monkeypatch.setattr(
        "app.controllers.categories_controller.category_repository.delete_owned",
        lambda *args: writes.append(args),
    )

    response = action_client.post("/categories/9/delete")

    assert response.status_code == 400
    assert writes == []


def test_invalid_form_input_does_not_change_data(monkeypatch, action_client):
    writes = []
    monkeypatch.setattr(
        "app.controllers.categories_controller.category_repository.create",
        lambda category: writes.append(category),
    )

    response = action_client.post(
        "/categories/new",
        data={"csrf_token": csrf_token(action_client), "name": "", "color": "not-a-color"},
    )

    assert response.status_code == 200
    assert writes == []
    assert b"This field is required." in response.data
    assert b"six-digit hexadecimal color" in response.data


def test_invalid_foreign_key_choice_is_not_converted_to_none(
    monkeypatch, action_client
):
    writes = []
    monkeypatch.setattr(
        "app.controllers.topics_controller.category_repository.list_for_user",
        lambda user_id: [],
    )
    monkeypatch.setattr(
        "app.controllers.topics_controller.topic_repository.create",
        lambda topic: writes.append(topic),
    )

    response = action_client.post(
        "/topics/new",
        data={
            "csrf_token": csrf_token(action_client),
            "title": "Access control",
            "category_id": "999",
            "status": "planned",
            "priority": "medium",
        },
    )

    assert response.status_code == 200
    assert writes == []
    assert b"Not a valid choice." in response.data


def test_invalid_datetime_is_not_converted_to_none(monkeypatch, action_client):
    writes = []
    monkeypatch.setattr(
        "app.controllers.scheduled_tasks_controller.scheduled_task_repository.list_visible",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        "app.controllers.scheduled_tasks_controller.scheduled_task_service.create_task",
        lambda *args, **kwargs: writes.append(args),
    )

    response = action_client.post(
        "/scheduled-tasks/",
        data={
            "csrf_token": csrf_token(action_client),
            "title": "Review report",
            "task_type": "review",
            "due_at": "not-a-date",
            "scope": "personal",
        },
    )

    assert response.status_code == 200
    assert writes == []
    assert b"Not a valid datetime value." in response.data


def test_successful_create_uses_post_redirect_get(monkeypatch, action_client):
    writes = []
    monkeypatch.setattr(
        "app.controllers.categories_controller.category_repository.create",
        lambda category: writes.append(category) or category,
    )
    monkeypatch.setattr(
        "app.controllers.categories_controller.log_audit", lambda *args: None
    )

    response = action_client.post(
        "/categories/new",
        data={
            "csrf_token": csrf_token(action_client),
            "name": "Web Security",
            "description": "Practice topics",
            "color": "#2563eb",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/categories/")
    assert len(writes) == 1


def test_sensitive_export_is_post_then_read_only_download(monkeypatch, action_client):
    audits = []
    monkeypatch.setattr(
        "app.controllers.backup_controller.export_service.record_personal_export",
        lambda export_format, context: audits.append(export_format),
    )
    monkeypatch.setattr(
        "app.controllers.backup_controller.export_service.personal_data",
        lambda user_id: {"user": {"id": user_id}},
    )

    assert action_client.get("/backup/personal.json").status_code == 405
    response = action_client.post(
        "/backup/personal.json", data={"csrf_token": csrf_token(action_client)}
    )

    assert response.status_code == 302
    assert "/backup/download/" in response.headers["Location"]
    assert audits == ["json"]

    download = action_client.get(response.headers["Location"])
    assert download.status_code == 200
    assert audits == ["json"]


def test_controllers_do_not_read_request_form_directly():
    controller_dir = PROJECT_ROOT / "app" / "controllers"
    for path in controller_dir.glob("*_controller.py"):
        assert "request.form" not in path.read_text(encoding="utf-8"), path.name


def test_every_literal_post_form_contains_csrf_markup():
    post_form = re.compile(
        r"<form\b(?=[^>]*\bmethod=[\"']post[\"'])[^>]*>.*?</form>",
        re.IGNORECASE | re.DOTALL,
    )
    template_dir = PROJECT_ROOT / "app" / "templates"

    for path in template_dir.rglob("*.html"):
        source = path.read_text(encoding="utf-8")
        for form_markup in post_form.findall(source):
            assert "csrf_token" in form_markup or ".hidden_tag()" in form_markup, path
