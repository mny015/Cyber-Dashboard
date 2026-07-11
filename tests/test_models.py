import inspect
import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from pathlib import Path
from types import NoneType
from typing import get_args, get_type_hints

import pytest

from app.models import MODEL_REGISTRY, Notification, User
from app.models.note_access_request import NoteAccessRequest


def schema_contract():
    contract_path = Path(__file__).parent / "contracts" / "schema_contract.json"
    return json.loads(contract_path.read_text(encoding="utf-8"))["tables"]


def sample_value(column_name, definition):
    if definition["nullable"]:
        return None
    column_type = definition["type"]
    if column_type == "tinyint":
        return 1
    if column_type == "int":
        return 7
    if column_type == "datetime":
        return datetime(2026, 7, 11, 9, 30)
    if column_type == "date":
        return date(2026, 7, 11)
    if column_type == "longblob":
        return b"model-image"
    return f"{column_name}-value"


def test_model_registry_covers_every_application_table_and_column():
    contract = schema_contract()

    assert set(MODEL_REGISTRY) == set(contract)
    for table_name, model_type in MODEL_REGISTRY.items():
        assert model_type.TABLE_NAME == table_name
        assert set(model_type.COLUMNS) == set(contract[table_name]["columns"])


@pytest.mark.parametrize("model_type", MODEL_REGISTRY.values(), ids=lambda model: model.__name__)
def test_models_are_slotted_dataclasses_with_row_conversion(model_type):
    table_definition = schema_contract()[model_type.TABLE_NAME]
    row = {
        column_name: sample_value(column_name, definition)
        for column_name, definition in table_definition["columns"].items()
    }
    row["ignored_join_alias"] = "not model data"

    instance = model_type.from_row(row)

    assert is_dataclass(model_type)
    assert "__slots__" in model_type.__dict__
    assert isinstance(instance, model_type)
    assert not hasattr(instance, "ignored_join_alias")
    for field in fields(model_type):
        if field.name not in row:
            continue
        if table_definition["columns"][field.name]["type"] == "tinyint":
            assert isinstance(getattr(instance, field.name), bool)
        else:
            assert getattr(instance, field.name) == row[field.name]


def test_nullable_database_columns_use_optional_python_types():
    contract = schema_contract()

    for table_name, model_type in MODEL_REGISTRY.items():
        type_hints = get_type_hints(model_type)
        for column_name, definition in contract[table_name]["columns"].items():
            if definition["nullable"]:
                assert NoneType in get_args(type_hints[column_name]), (
                    f"{model_type.__name__}.{column_name} must allow None"
                )


@pytest.mark.parametrize("model_type", MODEL_REGISTRY.values(), ids=lambda model: model.__name__)
def test_from_row_handles_missing_rows_and_rejects_non_mappings(model_type):
    assert model_type.from_row(None) is None
    with pytest.raises(TypeError, match="mappings"):
        model_type.from_row([("id", 1)])


def test_from_rows_preserves_order():
    users = User.from_rows(
        [
            {"id": 2, "email": "second@example.com"},
            {"id": 1, "email": "first@example.com"},
        ]
    )

    assert [user.id for user in users] == [2, 1]
    assert [user.email for user in users] == ["second@example.com", "first@example.com"]


def test_joined_projection_fields_are_explicit_and_unknown_fields_are_ignored():
    request = NoteAccessRequest.from_row(
        {
            "id": 4,
            "topic_id": 8,
            "status": "pending",
            "topic_title": "Web Security",
            "admin_name": "Admin",
            "unexpected": "discard me",
        }
    )

    assert request.topic_title == "Web Security"
    assert request.admin_name == "Admin"
    assert not hasattr(request, "unexpected")


def test_notification_is_a_read_model_for_note_access_requests():
    notification = Notification.from_row(
        {"id": 5, "topic_id": 9, "status": "pending", "topic_title": "SQLi"}
    )

    assert isinstance(notification, NoteAccessRequest)
    assert notification.TABLE_NAME == "note_access_requests"
    assert notification.topic_title == "SQLi"


def test_user_remains_flask_login_compatible_without_persistence_methods():
    user = User.from_row(
        {
            "id": 42,
            "email": "student@example.com",
            "role": "admin",
            "is_banned": 0,
            "mfa_enabled": 1,
        }
    )

    assert user.get_id() == "42"
    assert user.is_admin is True
    assert user.mfa_enabled is True


def test_models_do_not_expose_active_record_operations():
    forbidden_methods = {"save", "delete", "query", "refresh", "reload"}

    for model_type in MODEL_REGISTRY.values():
        assert forbidden_methods.isdisjoint(dir(model_type))


def test_model_modules_do_not_import_database_or_flask_request_state():
    forbidden_text = (
        "utils.db",
        "pymysql",
        "flask.request",
        "flask.session",
        "current_user",
    )

    for model_type in MODEL_REGISTRY.values():
        source = inspect.getsource(inspect.getmodule(model_type))
        assert not any(text in source for text in forbidden_text)
