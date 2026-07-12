"""Unit tests for business workflows and their transaction boundaries."""

from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.models import Note, User
from app.services import auth_service, export_service, note_service, notification_service
from app.services import user_management_service
from app.services.audit_service import AuditContext
from app.services.exceptions import LastAdministratorError
from app.utils.database.connection import MySQLConnectionPool
from app.utils.database.transaction import transaction


class ServiceCursor:
    def __init__(self, fail_on_execute=None):
        self.fail_on_execute = fail_on_execute
        self.execute_count = 0
        self.rowcount = 1
        self.lastrowid = 81

    def execute(self, _sql, _params=None):
        self.execute_count += 1
        if self.execute_count == self.fail_on_execute:
            raise RuntimeError("audit insert failed")
        return self.rowcount

    def close(self):
        return None


class ServiceConnection:
    def __init__(self, cursor):
        self.open = True
        self.cursor_instance = cursor
        self.commit_count = 0
        self.rollback_count = 0

    def ping(self, reconnect=False):
        return None

    def cursor(self):
        return self.cursor_instance

    def begin(self):
        return None

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.open = False


def test_service_modules_do_not_depend_on_flask_request_handling():
    service_dir = Path(__file__).resolve().parents[1] / "app" / "services"
    for path in service_dir.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "from flask" not in source
        assert "import flask" not in source


def test_note_creation_uses_one_database_for_write_and_audit(monkeypatch):
    cursor = object()
    database = object()
    calls = []

    @contextmanager
    def fake_transaction():
        yield cursor

    monkeypatch.setattr(note_service, "transaction", fake_transaction)
    monkeypatch.setattr(note_service.db, "using", lambda value: database)
    monkeypatch.setattr(
        note_service.note_repository,
        "create",
        lambda note, database=None: calls.append(("create", database))
        or Note(id=9, title=note.title),
    )
    monkeypatch.setattr(
        note_service.audit_service,
        "record",
        lambda *args, **kwargs: calls.append(("audit", args[-1])),
    )

    note = note_service.create_note(4, "Title", "Body", None, AuditContext(actor_id=4))

    assert note.id == 9
    assert calls == [("create", database), ("audit", database)]


def test_note_creation_rolls_back_when_audit_insert_fails(monkeypatch):
    cursor = ServiceCursor(fail_on_execute=2)
    raw_connection = ServiceConnection(cursor)
    pool = MySQLConnectionPool(
        {
            "host": "test",
            "port": 3306,
            "user": "test",
            "password": "test",
            "database": "test",
            "charset": "utf8mb4",
            "autocommit": False,
        },
        max_size=1,
        connect_factory=lambda **_kwargs: raw_connection,
    )
    monkeypatch.setattr(note_service, "transaction", lambda: transaction(pool))

    with pytest.raises(RuntimeError, match="audit insert failed"):
        note_service.create_note(4, "Title", "Body", None, AuditContext(actor_id=4))

    assert raw_connection.commit_count == 0
    assert raw_connection.rollback_count >= 1


def test_last_active_admin_cannot_be_banned(monkeypatch):
    user = User(id=7, email="admin@example.com", role="admin")
    database = object()

    @contextmanager
    def fake_transaction():
        yield object()

    monkeypatch.setattr(user_management_service, "transaction", fake_transaction)
    monkeypatch.setattr(user_management_service.db, "using", lambda _cursor: database)
    monkeypatch.setattr(
        user_management_service.user_repository,
        "find_by_id",
        lambda _user_id, database=None: user,
    )
    monkeypatch.setattr(
        user_management_service.user_repository,
        "count_other_active_admins",
        lambda _user_id, database=None: 0,
    )

    with pytest.raises(LastAdministratorError):
        user_management_service.set_banned(7, 3, True, AuditContext(actor_id=3))


def test_note_access_approval_records_audit_in_same_transaction(monkeypatch):
    cursor = object()
    database = object()
    calls = []

    @contextmanager
    def fake_transaction():
        yield cursor

    monkeypatch.setattr(notification_service, "transaction", fake_transaction)
    monkeypatch.setattr(notification_service.db, "using", lambda _cursor: database)
    monkeypatch.setattr(
        notification_service.notification_repository,
        "approve_owned",
        lambda request_id, owner_id, note_id, cursor=None: calls.append(
            ("approve", request_id, owner_id, note_id, cursor)
        )
        or 1,
    )
    monkeypatch.setattr(
        notification_service.audit_service,
        "record",
        lambda *args, **kwargs: calls.append(("audit", args[-1])),
    )

    notification_service.approve_request(5, 8, 13, AuditContext(actor_id=8))

    assert calls == [("approve", 5, 8, 13, cursor), ("audit", database)]


def test_personal_export_uses_privacy_scoped_repository_and_audits(monkeypatch):
    calls = []
    monkeypatch.setattr(
        export_service.backup_repository,
        "personal_data",
        lambda user_id: calls.append(("data", user_id)) or {"notes": []},
    )
    monkeypatch.setattr(
        export_service.audit_service,
        "record",
        lambda action, details, context: calls.append((action, details, context.actor_id)),
    )

    result = export_service.personal_export(11, "zip", AuditContext(actor_id=11))

    assert result == {"notes": []}
    assert calls == [
        ("data", 11),
        ("personal_backup_exported", "Exported personal data as CSV archive", 11),
    ]


def test_account_lockout_comparison_is_deterministic():
    now = datetime(2026, 7, 12, 12, 0, 0)
    user = User(locked_until=now + timedelta(minutes=1))

    assert auth_service.is_account_locked(user, now=now)
    user.locked_until = now - timedelta(seconds=1)
    assert not auth_service.is_account_locked(user, now=now)
