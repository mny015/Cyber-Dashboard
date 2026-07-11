import pytest

from app.utils.database import (
    InvalidNamedQueryNameError,
    NamedQueryError,
    NamedQueryNotFoundError,
    NamedQueryParameterError,
    clear_named_query_cache,
    load_named_query,
)
from app.utils.database.query_builder import Database


class RecordingDatabase(Database):
    def __init__(self):
        self.calls = []
        self.all_result = [{"topics": 4}]
        self.one_result = {"topics": 4}

    def _fetch_all(self, sql, params):
        self.calls.append(("all", sql, params))
        return self.all_result

    def _fetch_one(self, sql, params):
        self.calls.append(("one", sql, params))
        return self.one_result


def setup_function():
    clear_named_query_cache()


def test_valid_query_loading_uses_cached_utf8_sql():
    first = load_named_query("user_dashboard_metrics")
    second = load_named_query("user_dashboard_metrics")

    assert first == second
    assert "FROM topics" in first
    assert "%(user_id)s" in first


def test_missing_query_has_a_clear_error():
    with pytest.raises(NamedQueryNotFoundError, match="does not exist"):
        load_named_query("query_that_is_not_present")


@pytest.mark.parametrize(
    "query_name",
    [
        "",
        "../admin_dashboard_metrics",
        "..\\admin_dashboard_metrics",
        "admin_dashboard_metrics.sql",
        "/admin_dashboard_metrics",
        "Admin_Dashboard_Metrics",
        "admin-dashboard-metrics",
    ],
)
def test_invalid_and_traversal_query_names_are_rejected(query_name):
    with pytest.raises(InvalidNamedQueryNameError):
        load_named_query(query_name)


def test_named_query_executes_with_parameters_kept_separate():
    database = RecordingDatabase()
    user_id = "7 OR 1=1"

    result = database.named_query("user_dashboard_metrics", {"user_id": user_id})

    assert result == [{"topics": 4}]
    call_type, sql, parameters = database.calls[0]
    assert call_type == "all"
    assert user_id not in sql
    assert parameters == {"user_id": user_id}


def test_named_query_can_fetch_one_dictionary():
    database = RecordingDatabase()

    result = database.named_query(
        "admin_dashboard_metrics",
        {"backup_pattern": "%backup%", "export_pattern": "%export%"},
        fetch="one",
    )

    assert result == {"topics": 4}
    assert database.calls[0][0] == "one"


def test_named_parameters_must_match_sql_placeholders():
    database = RecordingDatabase()

    with pytest.raises(NamedQueryParameterError, match="Missing"):
        database.named_query("user_dashboard_metrics", {})
    with pytest.raises(NamedQueryParameterError, match="Unexpected"):
        database.named_query(
            "user_dashboard_metrics",
            {"user_id": 7, "raw_order_by": "created_at DESC"},
        )

    assert database.calls == []


def test_named_query_rejects_unknown_fetch_modes():
    database = RecordingDatabase()

    with pytest.raises(NamedQueryError, match="fetch mode"):
        database.named_query(
            "user_dashboard_metrics",
            {"user_id": 7},
            fetch="cursor",
        )

    assert database.calls == []
