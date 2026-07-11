import json
from pathlib import Path

import pytest

from app.utils.database.query_builder import (
    TABLE_COLUMNS,
    Database,
    InvalidIdentifierError,
    InvalidOperatorError,
    PaginationResult,
    QueryBuilderError,
    UnsafeQueryError,
    WriteResult,
)


class RecordingDatabase(Database):
    """Capture generated SQL so unit tests never need a live database."""

    def __init__(self):
        self.calls = []
        self.all_result = []
        self.one_results = []
        self.write_result = WriteResult(1, 7)

    def _fetch_all(self, sql, params):
        self.calls.append(("all", sql, params))
        return self.all_result

    def _fetch_one(self, sql, params):
        self.calls.append(("one", sql, params))
        return self.one_results.pop(0) if self.one_results else None

    def _execute(self, sql, params):
        self.calls.append(("execute", sql, params))
        return self.write_result

    def _executemany(self, sql, params):
        self.calls.append(("executemany", sql, params))
        return self.write_result


@pytest.fixture
def database():
    return RecordingDatabase()


def test_generated_select_sql_and_parameters(database):
    database.all_result = [{"id": 3, "email": "active@example.com"}]

    result = (
        database.table("users")
        .select("id", "email")
        .where("role", "=", "active")
        .order_by("created_at", "DESC")
        .limit(20)
        .all()
    )

    assert result == [{"id": 3, "email": "active@example.com"}]
    assert database.calls == [
        (
            "all",
            "SELECT `id`, `email` FROM `users` WHERE `role` = %s "
            "ORDER BY `created_at` DESC LIMIT %s",
            ("active", 20),
        )
    ]


def test_multiple_where_and_or_conditions(database):
    (
        database.table("users")
        .where("role", "=", "user")
        .where("is_banned", "=", False)
        .or_where("email", "LIKE", "%@example.com")
        .all()
    )

    assert database.calls[0] == (
        "all",
        "SELECT * FROM `users` WHERE `role` = %s AND `is_banned` = %s "
        "OR `email` LIKE %s",
        ("user", False, "%@example.com"),
    )


def test_in_and_null_predicates(database):
    (
        database.table("topics")
        .where_in("status", ["learning", "reviewing"])
        .where_null("category_id")
        .where_not_null("updated_at")
        .all()
    )

    assert database.calls[0] == (
        "all",
        "SELECT * FROM `topics` WHERE `status` IN (%s, %s) "
        "AND `category_id` IS NULL AND `updated_at` IS NOT NULL",
        ("learning", "reviewing"),
    )


def test_inner_and_left_joins(database):
    (
        database.table("topics")
        .select("topics.id", "categories.name", "users.email")
        .join("users", "topics.owner_id", "=", "users.id")
        .left_join("categories", "topics.category_id", "=", "categories.id")
        .all()
    )

    assert database.calls[0] == (
        "all",
        "SELECT `topics`.`id`, `categories`.`name`, `users`.`email` FROM `topics` "
        "INNER JOIN `users` ON `topics`.`owner_id` = `users`.`id` "
        "LEFT JOIN `categories` ON `topics`.`category_id` = `categories`.`id`",
        (),
    )


def test_group_having_order_limit_and_offset(database):
    (
        database.table("topics")
        .select("status")
        .group_by("status")
        .having("status", "!=", "archived")
        .order_by("status", "ASC")
        .limit(10)
        .offset(20)
        .all()
    )

    assert database.calls[0] == (
        "all",
        "SELECT `status` FROM `topics` GROUP BY `status` HAVING `status` != %s "
        "ORDER BY `status` ASC LIMIT %s OFFSET %s",
        ("archived", 10, 20),
    )


def test_first_count_and_exists(database):
    database.one_results = [{"id": 4}, {"aggregate": 3}, {"exists_value": 1}]
    query = database.table("notes").where("owner_id", "=", 9)

    assert query.first() == {"id": 4}
    assert query.count() == 3
    assert query.exists() is True
    assert database.calls == [
        ("one", "SELECT * FROM `notes` WHERE `owner_id` = %s LIMIT %s", (9, 1)),
        (
            "one",
            "SELECT COUNT(*) AS `aggregate` FROM "
            "(SELECT 1 FROM `notes` WHERE `owner_id` = %s) AS `count_query`",
            (9,),
        ),
        (
            "one",
            "SELECT 1 AS `exists_value` FROM `notes` WHERE `owner_id` = %s LIMIT %s",
            (9, 1),
        ),
    ]


def test_paginate_returns_typed_result(database):
    database.one_results = [{"aggregate": 43}]
    database.all_result = [{"id": 41}, {"id": 42}, {"id": 43}]

    result = database.table("topics").order_by("id").paginate(page=3, per_page=20)

    assert result == PaginationResult(
        items=[{"id": 41}, {"id": 42}, {"id": 43}],
        total=43,
        page=3,
        per_page=20,
        pages=3,
    )
    assert result.has_previous is True
    assert result.has_next is False
    assert database.calls[-1] == (
        "all",
        "SELECT * FROM `topics` ORDER BY `id` ASC LIMIT %s OFFSET %s",
        (20, 40),
    )


def test_insert_uses_parameterized_values(database):
    result = database.table("categories").insert(
        {"name": "Web", "description": "Web security", "owner_id": 2}
    )

    assert result == WriteResult(1, 7)
    assert database.calls[0] == (
        "execute",
        "INSERT INTO `categories` (`name`, `description`, `owner_id`) "
        "VALUES (%s, %s, %s)",
        ("Web", "Web security", 2),
    )


def test_insert_many_preserves_column_order(database):
    database.table("contacts").insert_many(
        [
            {"name": "A", "email": "a@example.com", "owner_id": 1},
            {"email": "b@example.com", "owner_id": 2, "name": "B"},
        ]
    )

    assert database.calls[0] == (
        "executemany",
        "INSERT INTO `contacts` (`name`, `email`, `owner_id`) VALUES (%s, %s, %s)",
        (("A", "a@example.com", 1), ("B", "b@example.com", 2)),
    )


def test_update_uses_set_values_before_where_values(database):
    database.table("topics").where("id", "=", 5).update(
        {"title": "Revised", "status": "reviewing"}
    )

    assert database.calls[0] == (
        "execute",
        "UPDATE `topics` SET `title` = %s, `status` = %s WHERE `id` = %s",
        ("Revised", "reviewing", 5),
    )


def test_delete_is_parameterized(database):
    database.table("notes").where("id", "=", 12).where("owner_id", "=", 4).delete()

    assert database.calls[0] == (
        "execute",
        "DELETE FROM `notes` WHERE `id` = %s AND `owner_id` = %s",
        (12, 4),
    )


def test_values_never_enter_generated_sql(database):
    malicious_value = "active' OR 1=1 --"
    database.table("users").where("role", "=", malicious_value).all()

    _kind, sql, params = database.calls[0]
    assert malicious_value not in sql
    assert params == (malicious_value,)


@pytest.mark.parametrize(
    ("operation", "expected_exception"),
    [
        (lambda database: database.table("users; DROP TABLE users"), InvalidIdentifierError),
        (lambda database: database.table("missing_table"), InvalidIdentifierError),
        (lambda database: database.table("users").select("password"), InvalidIdentifierError),
        (lambda database: database.table("users").where("id", "OR 1=1", 1), InvalidOperatorError),
        (lambda database: database.table("users").order_by("id", "sideways"), InvalidOperatorError),
    ],
)
def test_invalid_identifiers_and_operators_are_rejected(database, operation, expected_exception):
    with pytest.raises(expected_exception):
        result = operation(database)
        if hasattr(result, "all"):
            result.all()


def test_rejected_join_does_not_mutate_builder(database):
    query = database.table("topics")

    with pytest.raises(InvalidIdentifierError):
        query.join("users", "topics.owner_id", "=", "categories.id")

    query.all()
    assert database.calls[0] == ("all", "SELECT * FROM `topics`", ())


def test_update_without_where_is_rejected(database):
    with pytest.raises(UnsafeQueryError, match="UPDATE requires"):
        database.table("users").update({"is_banned": True})

    assert database.calls == []


def test_delete_without_where_is_rejected(database):
    with pytest.raises(UnsafeQueryError, match="DELETE requires"):
        database.table("users").delete()

    assert database.calls == []


def test_invalid_collections_and_pagination_are_rejected(database):
    with pytest.raises(QueryBuilderError):
        database.table("users").where_in("id", [])
    with pytest.raises(QueryBuilderError):
        database.table("users").offset(4).all()
    with pytest.raises(QueryBuilderError):
        database.table("users").paginate(page=0)


def test_query_builder_registry_matches_schema_contract():
    contract_path = Path(__file__).parent / "contracts" / "schema_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    expected_tables = {
        table_name: set(table_definition["columns"])
        for table_name, table_definition in contract["tables"].items()
    }

    assert set(TABLE_COLUMNS) == set(expected_tables)
    for table_name, expected_columns in expected_tables.items():
        assert TABLE_COLUMNS[table_name] == expected_columns
