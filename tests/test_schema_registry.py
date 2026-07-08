import pytest

from utils.schema import (
    build_insert_sql,
    build_update_sql,
    get_column_alters,
    get_create_statements,
    get_table,
    quote_identifier,
)


def test_schema_registry_exposes_table_metadata():
    users = get_table("users")

    assert users.primary_key == ("id",)
    assert "email" in users.columns
    assert "profile_image -> profile_images.image_hash" in users.foreign_keys
    assert "CREATE TABLE IF NOT EXISTS users" in users.create_sql


def test_create_statements_keep_dependency_order():
    statements = get_create_statements()

    assert "CREATE TABLE IF NOT EXISTS profile_images" in statements[0]
    assert "CREATE TABLE IF NOT EXISTS lab_platforms" in statements[1]
    assert any("CREATE TABLE IF NOT EXISTS notes" in statement for statement in statements)
    assert len(statements) >= 15


def test_column_alters_are_centralized():
    user_alters = get_column_alters("users")
    all_alters = get_column_alters()

    assert "failed_login_count" in user_alters
    assert "users" in all_alters
    assert "lab_references" in all_alters


def test_quote_identifier_allows_only_known_schema_identifiers():
    assert quote_identifier("users") == "`users`"
    assert quote_identifier("email") == "`email`"

    with pytest.raises(ValueError):
        quote_identifier("users; DROP TABLE users")

    with pytest.raises(ValueError):
        quote_identifier("unknown_table")


def test_build_insert_sql_uses_known_table_and_columns_only():
    sql = build_insert_sql("categories", ["name", "description", "color", "owner_id"])

    assert sql == "INSERT INTO `categories` (`name`, `description`, `color`, `owner_id`) VALUES (%s, %s, %s, %s)"

    with pytest.raises(ValueError):
        build_insert_sql("categories", ["name", "not_a_column"])

    with pytest.raises(ValueError):
        build_insert_sql("not_a_table", ["name"])


def test_build_update_sql_uses_known_mutable_columns_only():
    sql = build_update_sql("topics", ["title", "updated_at"], "id = %s AND owner_id = %s")

    assert sql == "UPDATE `topics` SET `title` = %s, `updated_at` = %s WHERE id = %s AND owner_id = %s"

    with pytest.raises(ValueError):
        build_update_sql("topics", ["owner_id"], "id = %s")

    with pytest.raises(ValueError):
        build_update_sql("topics", ["title"], "id = %s; DROP TABLE topics")
