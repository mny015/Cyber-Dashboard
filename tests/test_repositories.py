from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from flask import Flask

from app.models import Category, Contact, Note, User
from app.repositories import (
    category_repository,
    contact_repository,
    note_repository,
    topic_repository,
    user_repository,
)
from app.utils.database.query_builder import Database, WriteResult


class RecordingDatabase(Database):
    def __init__(self):
        self.calls = []
        self.one_result = None
        self.all_result = []

    def _fetch_one(self, sql, params):
        self.calls.append(("one", sql, params))
        return self.one_result

    def _fetch_all(self, sql, params):
        self.calls.append(("all", sql, params))
        return self.all_result

    def _execute(self, sql, params):
        self.calls.append(("execute", sql, params))
        return WriteResult(1, 12)


def test_user_repository_returns_user_models(monkeypatch):
    database = RecordingDatabase()
    database.one_result = {"id": 4, "email": "user@example.com"}
    monkeypatch.setattr(user_repository, "db", database)

    user = user_repository.find_by_email("user@example.com")

    assert isinstance(user, User)
    assert database.calls[0] == (
        "one",
        "SELECT * FROM `users` WHERE `email` = %s LIMIT %s",
        ("user@example.com", 1),
    )


def test_user_repository_encrypts_mfa_secret_before_write(monkeypatch):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="repository-secret",
        MFA_ENCRYPTION_KEY=Fernet.generate_key().decode("ascii"),
    )
    database = RecordingDatabase()

    with app.app_context():
        user_repository.set_mfa_secret(4, "JBSWY3DPEHPK3PXP", database=database)

    _kind, sql, params = database.calls[0]
    assert sql.startswith("UPDATE `users` SET")
    assert params[0].startswith("mfa:v1:")
    assert "JBSWY3DPEHPK3PXP" not in params[0]


@pytest.mark.parametrize(
    ("repository", "model", "table_name"),
    [
        (category_repository, Category(id=3, owner_id=8), "categories"),
        (contact_repository, Contact(id=3, owner_id=8), "contacts"),
    ],
)
def test_owned_repository_lookup_filters_id_owner_and_soft_delete(
    monkeypatch, repository, model, table_name
):
    database = RecordingDatabase()
    database.one_result = {
        "id": model.id,
        "owner_id": model.owner_id,
        "is_deleted": 0,
    }
    monkeypatch.setattr(repository, "db", database)

    result = repository.find_owned(model.id, model.owner_id)

    assert result.id == model.id
    _kind, sql, params = database.calls[0]
    assert sql == (
        f"SELECT * FROM `{table_name}` WHERE `id` = %s AND `owner_id` = %s "
        "AND `is_deleted` = %s LIMIT %s"
    )
    assert params == (3, 8, False, 1)


def test_topic_permission_check_is_owner_scoped(monkeypatch):
    database = RecordingDatabase()
    database.one_result = {"exists_value": 1}
    monkeypatch.setattr(topic_repository, "db", database)

    assert topic_repository.exists_owned(5, 9) is True

    _kind, sql, params = database.calls[0]
    assert "`id` = %s AND `owner_id` = %s AND `is_deleted` = %s" in sql
    assert params == (5, 9, False, 1)


def test_note_update_repeats_ownership_in_write_query(monkeypatch):
    database = RecordingDatabase()
    monkeypatch.setattr(note_repository, "db", database)
    note = Note(id=6, title="Updated", body="Body", owner_id=11)

    note_repository.update_owned(note, 11)

    _kind, sql, params = database.calls[0]
    assert sql.startswith("UPDATE `notes` SET")
    assert "WHERE `id` = %s AND `owner_id` = %s AND `is_deleted` = %s" in sql
    assert params[-3:] == (6, 11, False)


def test_repository_modules_do_not_access_http_or_flask_state():
    repository_root = Path(__file__).parents[1] / "app" / "repositories"
    forbidden = (
        "from flask",
        "flask_login",
        "current_user",
        "request.",
        "session",
        "flash(",
        "redirect(",
        "render_template(",
    )

    for path in repository_root.glob("*_repository.py"):
        source = path.read_text(encoding="utf-8")
        assert not any(token in source for token in forbidden), path.name


def test_routes_and_controllers_do_not_contain_runtime_sql_or_legacy_db_helpers():
    app_root = Path(__file__).parents[1] / "app"
    checked_paths = list((app_root / "routes").glob("*.py"))
    checked_paths.extend((app_root / "controllers").glob("*.py"))

    for path in checked_paths:
        source = path.read_text(encoding="utf-8")
        assert "utils.db" not in source, path.name
        assert not any(
            keyword in source
            for keyword in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ")
        ), path.name
