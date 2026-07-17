import inspect
from dataclasses import is_dataclass

import pytest

from app.models import MODEL_REGISTRY, Notification, User
from app.models.note_access_request import NoteAccessRequest


def test_model_registry_has_unique_table_and_column_metadata():
    assert MODEL_REGISTRY
    assert len(MODEL_REGISTRY) == len(set(MODEL_REGISTRY))

    for table_name, model_type in MODEL_REGISTRY.items():
        assert model_type.TABLE_NAME == table_name
        assert model_type.COLUMNS
        assert len(model_type.COLUMNS) == len(set(model_type.COLUMNS))


@pytest.mark.parametrize("model_type", MODEL_REGISTRY.values(), ids=lambda model: model.__name__)
def test_models_are_slotted_dataclasses_with_row_conversion(model_type):
    instance = model_type.from_row({"id": 7, "ignored_join_alias": "discard"})

    assert is_dataclass(model_type)
    assert "__slots__" in model_type.__dict__
    assert isinstance(instance, model_type)
    assert not hasattr(instance, "ignored_join_alias")


def test_row_conversion_handles_missing_invalid_and_multiple_rows():
    assert User.from_row(None) is None
    with pytest.raises(TypeError, match="mappings"):
        User.from_row([("id", 1)])

    users = User.from_rows(
        [
            {"id": 2, "email": "second@example.com"},
            {"id": 1, "email": "first@example.com"},
        ]
    )
    assert [user.id for user in users] == [2, 1]
    assert [user.email for user in users] == [
        "second@example.com",
        "first@example.com",
    ]


def test_joined_read_models_and_flask_login_user_conversion():
    notification = Notification.from_row(
        {"id": 5, "topic_id": 9, "status": "pending", "topic_title": "SQLi"}
    )
    user = User.from_row(
        {
            "id": 42,
            "email": "student@example.com",
            "role": "admin",
            "is_banned": 0,
            "mfa_enabled": 1,
        }
    )

    assert isinstance(notification, NoteAccessRequest)
    assert notification.topic_title == "SQLi"
    assert user.get_id() == "42"
    assert user.is_admin is True
    assert user.mfa_enabled is True


def test_models_remain_passive_and_do_not_import_request_or_database_state():
    forbidden_methods = {"save", "delete", "query", "refresh", "reload"}
    forbidden_text = (
        "utils.db",
        "pymysql",
        "flask.request",
        "flask.session",
        "current_user",
    )

    for model_type in MODEL_REGISTRY.values():
        assert forbidden_methods.isdisjoint(dir(model_type))
        source = inspect.getsource(inspect.getmodule(model_type))
        assert not any(text in source for text in forbidden_text)
