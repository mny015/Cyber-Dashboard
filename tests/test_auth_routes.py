from datetime import datetime, timedelta
from pathlib import Path

import pytest
from flask import Blueprint, redirect, render_template, url_for
from werkzeug.security import generate_password_hash

from app.extensions import limiter, login_manager
from app.models import User
from app.routes.auth import auth_bp


@pytest.fixture()
def fake_auth_app():
    from flask import Flask

    template_dir = Path(__file__).resolve().parents[1] / "app" / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.config.update(
        SECRET_KEY="test-secret-key",
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
    )

    login_manager.init_app(app)
    if limiter:
        limiter.init_app(app)

    dashboard_bp = Blueprint("dashboard", __name__)

    @dashboard_bp.route("/")
    def index():
        return render_template("index.html")

    @dashboard_bp.route("/dashboard")
    def dashboard():
        return "dashboard"

    @dashboard_bp.route("/user/dashboard")
    def user_dashboard():
        return "user dashboard"

    @dashboard_bp.route("/admin/dashboard")
    def admin_dashboard():
        return "admin dashboard"

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)

    @app.route("/login")
    def login_page():
        return redirect(url_for("auth.login"))

    return app


@pytest.fixture()
def fake_auth_client(fake_auth_app):
    return fake_auth_app.test_client()


def make_user_row(
    email="student@example.com",
    password="CorrectPassword123!",
    role="user",
    is_banned=False,
    mfa_enabled=False,
):
    return {
        "id": 42,
        "email": email,
        "password_hash": generate_password_hash(password),
        "display_name": "Test Student",
        "role": role,
        "is_banned": int(is_banned),
        "mfa_secret": None,
        "mfa_enabled": int(mfa_enabled),
        "auth_version": 0,
        "failed_login_count": 0,
        "last_failed_login_at": None,
        "locked_until": None,
    }


def test_home_page_renders_without_database(fake_auth_client):
    response = fake_auth_client.get("/")

    assert response.status_code == 200
    assert b"Cyber Dashboard" in response.data


def test_login_page_renders_without_database(fake_auth_client):
    response = fake_auth_client.get("/login", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"name@example.com" in response.data


def test_successful_login_uses_mocked_database_response(monkeypatch, fake_auth_client):
    user = User.from_row(make_user_row())
    reset_calls = []
    audit_calls = []

    monkeypatch.setattr("app.repositories.user_repository.find_by_email", lambda email: user)
    monkeypatch.setattr(
        "app.repositories.user_repository.reset_failed_logins",
        lambda user_id: reset_calls.append(user_id),
    )
    monkeypatch.setattr(
        "app.services.audit_service.record",
        lambda action, details="", context=None, database=None: audit_calls.append(
            (action, details, context)
        ),
    )

    response = fake_auth_client.post(
        "/auth/login",
        data={"email": "student@example.com", "password": "CorrectPassword123!"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/user/dashboard")
    assert reset_calls == [42]
    assert audit_calls[0][0] == "login"

    with fake_auth_client.session_transaction() as session:
        assert session["_user_id"] == "42"
        assert session["auth_version"] == 0


def test_failed_login_uses_mocked_database_response(monkeypatch, fake_auth_client):
    user = User.from_row(make_user_row())
    failure_calls = []
    audit_calls = []

    monkeypatch.setattr("app.repositories.user_repository.find_by_email", lambda email: user)
    monkeypatch.setattr(
        "app.repositories.user_repository.record_failed_login",
        lambda user_id, limit, minutes, cursor=None: failure_calls.append(
            (user_id, limit, minutes)
        ),
    )
    monkeypatch.setattr(
        "app.services.audit_service.record",
        lambda action, details="", context=None, database=None: audit_calls.append(
            (action, details, context)
        ),
    )

    from contextlib import contextmanager

    @contextmanager
    def fake_transaction():
        yield object()

    monkeypatch.setattr("app.services.auth_service.transaction", fake_transaction)
    monkeypatch.setattr("app.services.auth_service.db.using", lambda _cursor: object())

    response = fake_auth_client.post(
        "/auth/login",
        data={"email": "student@example.com", "password": "WrongPassword123!"},
    )

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    assert failure_calls == [(42, 5, 15)]
    assert audit_calls[0][0] == "login_failed"

    with fake_auth_client.session_transaction() as session:
        assert "_user_id" not in session


def test_locked_account_blocks_login_before_password_check(monkeypatch, fake_auth_client):
    user_row = make_user_row()
    user_row["locked_until"] = datetime.now() + timedelta(minutes=10)
    audit_calls = []

    monkeypatch.setattr(
        "app.repositories.user_repository.find_by_email",
        lambda email: User.from_row(user_row),
    )
    monkeypatch.setattr(
        "app.repositories.user_repository.record_failed_login",
        lambda *args: pytest.fail("locked accounts should not update login counters"),
    )
    monkeypatch.setattr(
        "app.services.audit_service.record",
        lambda action, details="", context=None, database=None: audit_calls.append(
            (action, details, context)
        ),
    )

    response = fake_auth_client.post(
        "/auth/login",
        data={"email": "student@example.com", "password": "CorrectPassword123!"},
    )

    assert response.status_code == 200
    assert b"Too many failed login attempts. Try again later." in response.data
    assert audit_calls[0][0] == "login_locked"

    with fake_auth_client.session_transaction() as session:
        assert "_user_id" not in session


def test_logout_rejects_get_requests(fake_auth_client):
    response = fake_auth_client.get("/auth/logout")

    assert response.status_code == 405


def test_logout_uses_post_request(monkeypatch, fake_auth_client):
    monkeypatch.setattr(
        "app.repositories.user_repository.find_by_id",
        lambda user_id: User.from_row(make_user_row()),
    )
    monkeypatch.setattr("app.routes.auth.log_audit", lambda *args, **kwargs: None)

    with fake_auth_client.session_transaction() as session:
        session["_user_id"] = "42"
        session["_fresh"] = True
        session["auth_version"] = 0

    response = fake_auth_client.post("/auth/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
    with fake_auth_client.session_transaction() as session:
        assert "_user_id" not in session
