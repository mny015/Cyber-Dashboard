"""Architecture and Flask-client tests for the HTTP controller layer."""

import ast
from collections import Counter
from pathlib import Path

import pytest
from flask import Flask

from app.extensions import csrf, login_manager
from app.models import User
from app.routes import register_blueprints

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROUTES_DIR = PROJECT_ROOT / "app" / "routes"
CONTROLLERS_DIR = PROJECT_ROOT / "app" / "controllers"
EXPECTED_BLUEPRINTS = {
    "admin",
    "api",
    "auth",
    "backup",
    "categories",
    "contacts",
    "dashboard",
    "labs",
    "notes",
    "notifications",
    "profile",
    "security",
    "tasks",
    "topics",
}


@pytest.fixture()
def controller_app():
    template_dir = PROJECT_ROOT / "app" / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.config.update(
        SECRET_KEY="controller-test-secret",
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    original_login_view = login_manager.login_view
    original_user_callback = login_manager._user_callback
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "login_stub"

    @login_manager.user_loader
    def load_user(user_id):
        return User(
            id=int(user_id),
            email="student@example.com",
            display_name="Student",
            role="user",
        )

    @app.route("/login")
    def login_stub():
        return "login"

    register_blueprints(app)
    yield app

    login_manager.login_view = original_login_view
    login_manager._user_callback = original_user_callback


@pytest.fixture()
def authenticated_controller_client(controller_app):
    client = controller_app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "9"
        session["_fresh"] = True
        session["auth_version"] = 0
    return client


def test_application_routes_are_unique_and_map_directly_to_controllers(app):
    application_rules = [rule for rule in app.url_map.iter_rules() if rule.endpoint != "static"]

    assert len(application_rules) == 72
    assert set(app.blueprints) == EXPECTED_BLUEPRINTS

    endpoint_counts = Counter(rule.endpoint for rule in application_rules)
    method_rule_counts = Counter(
        (rule.rule, method)
        for rule in application_rules
        for method in rule.methods - {"HEAD", "OPTIONS"}
    )
    assert all(count == 1 for count in endpoint_counts.values())
    assert all(count == 1 for count in method_rule_counts.values())

    for rule in application_rules:
        view = app.view_functions[rule.endpoint]
        while hasattr(view, "__wrapped__"):
            view = view.__wrapped__
        assert view.__module__.startswith("app.controllers."), rule.endpoint


def test_route_modules_only_define_blueprints_and_url_mappings():
    for path in ROUTES_DIR.glob("*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in tree.body)
        source = path.read_text(encoding="utf-8")
        assert ".route(" not in source
        assert ".add_url_rule(" in source
        assert "app.repositories" not in source
        assert "app.services" not in source
        assert "app.extensions" not in source

        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        flask_imports = {
            alias.name
            for node in imports
            if node.module == "flask"
            for alias in node.names
        }
        app_imports = {
            node.module
            for node in imports
            if node.module and node.module.startswith("app.")
        }
        assert flask_imports == {"Blueprint"}
        assert app_imports == {"app.controllers"}

        calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
        assert all(
            (isinstance(call, ast.Name) and call.id == "Blueprint")
            or (isinstance(call, ast.Attribute) and call.attr == "add_url_rule")
            for call in calls
        )


def test_controller_modules_have_no_blueprints_sql_or_database_connections():
    forbidden = (
        "Blueprint(",
        "cursor.execute(",
        "get_connection(",
        "db.table(",
        "db.named_query(",
        "CREATE TABLE",
        "ALTER TABLE",
    )
    for path in CONTROLLERS_DIR.glob("*_controller.py"):
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{path.name} contains {token}"
        assert "except Exception" not in source


def test_note_controller_rejects_invalid_form_before_service_call(
    monkeypatch, authenticated_controller_client
):
    writes = []
    monkeypatch.setattr(
        "app.controllers.notes_controller.topic_repository.list_active", lambda user_id: []
    )
    monkeypatch.setattr(
        "app.controllers.notes_controller.note_service.create_note",
        lambda *args: writes.append(args),
    )

    response = authenticated_controller_client.post(
        "/notes/new", data={"title": "", "body": ""}
    )

    assert response.status_code == 200
    assert b"This field is required." in response.data
    assert b'role="alert"' in response.data
    assert b'id="title-errors"' in response.data
    assert writes == []


def test_normal_user_cannot_read_another_profile_picture(
    monkeypatch, authenticated_controller_client
):
    admin_image_reads = []
    monkeypatch.setattr(
        "app.controllers.profile_controller.user_repository.find_profile_image",
        lambda image_hash: admin_image_reads.append(image_hash),
    )

    response = authenticated_controller_client.get(
        f"/profile/picture/{'a' * 64}"
    )

    assert response.status_code == 404
    assert admin_image_reads == []
