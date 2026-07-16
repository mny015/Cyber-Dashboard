"""Safety and relationship checks for the manual demo-data injector."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "docs" / "inject_test_data.py"
SPEC = importlib.util.spec_from_file_location("inject_test_data", SCRIPT_PATH)
injector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(injector)


def test_demo_definition_has_valid_cross_record_relationships():
    injector.validate_demo_definition()

    user_keys = {user["key"] for user in injector.DEMO_USERS}
    category_count = sum(len(user["categories"]) for user in injector.DEMO_USERS)
    lab_keys = {
        lab["key"]
        for user in injector.DEMO_USERS
        for category in user["categories"]
        for topic in category["topics"]
        for lab in topic["labs"]
    }

    assert user_keys == {"admin", "maya", "jordan", "samira"}
    assert category_count >= 6
    assert len(lab_keys) >= 10
    assert all(user_key in user_keys for user_key, _lab_key, _days in injector.LAB_COMPLETIONS)
    assert all(lab_key in lab_keys for _user_key, lab_key, _days in injector.LAB_COMPLETIONS)


def test_every_lab_is_correlated_with_a_topic_and_note():
    for user in injector.DEMO_USERS:
        for category in user["categories"]:
            for topic in category["topics"]:
                assert topic["note"]["title"]
                assert topic["note"]["body"]
                for lab in topic["labs"]:
                    assert lab["url"] in topic["note"]["body"]
                    expected_visibility = "public" if user["role"] == "admin" else "personal"
                    assert lab["visibility"] == expected_visibility


def test_target_validation_rejects_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    application = SimpleNamespace(config={"DB_NAME": "cyber_dashboard"})

    with pytest.raises(injector.DemoDataError, match="production"):
        injector.validate_target(application, "cyber_dashboard")


def test_target_validation_requires_exact_database_confirmation(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    application = SimpleNamespace(config={"DB_NAME": "cyber_dashboard"})

    with pytest.raises(injector.DemoDataError, match="does not match"):
        injector.validate_target(application, "another_database")

    assert injector.validate_target(application, "cyber_dashboard") == "cyber_dashboard"


def test_inject_function_validates_target_before_database_work(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    application = SimpleNamespace(config={"DB_NAME": "cyber_dashboard"})

    with pytest.raises(injector.DemoDataError, match="production"):
        injector.inject_demo_data(
            application,
            confirmed_database="cyber_dashboard",
            password="StrongDemoPassword1!",
        )
