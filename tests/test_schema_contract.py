import json
from collections import defaultdict
from pathlib import Path

from utils.db import get_connection


CONTRACT_PATH = Path(__file__).parent / "contracts" / "schema_contract.json"


def load_contract():
    with CONTRACT_PATH.open(encoding="utf-8") as contract_file:
        return json.load(contract_file)


def fetch_schema_rows(database_name):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            connected_database = cursor.fetchone()["database_name"]
            assert connected_database == database_name

            cursor.execute(
                """
                SELECT TABLE_NAME AS table_name, COLUMN_NAME AS column_name,
                       DATA_TYPE AS data_type, IS_NULLABLE AS is_nullable
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (database_name,),
            )
            columns = cursor.fetchall()

            cursor.execute(
                """
                SELECT TABLE_NAME AS table_name, INDEX_NAME AS index_name,
                       NON_UNIQUE AS non_unique, COLUMN_NAME AS column_name,
                       SEQ_IN_INDEX AS sequence_number
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
                """,
                (database_name,),
            )
            indexes = cursor.fetchall()

            cursor.execute(
                """
                SELECT TABLE_NAME AS table_name, CONSTRAINT_NAME AS constraint_name,
                       COLUMN_NAME AS column_name,
                       REFERENCED_TABLE_NAME AS referenced_table,
                       REFERENCED_COLUMN_NAME AS referenced_column,
                       ORDINAL_POSITION AS sequence_number
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION
                """,
                (database_name,),
            )
            foreign_keys = cursor.fetchall()
    finally:
        connection.close()

    return columns, indexes, foreign_keys


def group_columns(rows):
    grouped = defaultdict(dict)
    for row in rows:
        grouped[row["table_name"]][row["column_name"]] = {
            "type": row["data_type"].lower(),
            "nullable": row["is_nullable"] == "YES",
        }
    return grouped


def group_indexes(rows):
    grouped = defaultdict(lambda: defaultdict(list))
    uniqueness = defaultdict(dict)
    for row in rows:
        grouped[row["table_name"]][row["index_name"]].append(row["column_name"])
        uniqueness[row["table_name"]][row["index_name"]] = not bool(row["non_unique"])
    return grouped, uniqueness


def group_foreign_keys(rows):
    grouped = defaultdict(lambda: defaultdict(lambda: {"columns": [], "referenced_columns": []}))
    for row in rows:
        key = grouped[row["table_name"]][row["constraint_name"]]
        key["columns"].append(row["column_name"])
        key["referenced_table"] = row["referenced_table"]
        key["referenced_columns"].append(row["referenced_column"])
    return grouped


def test_mysql_schema_matches_frozen_contract(dedicated_test_database):
    contract = load_contract()["tables"]
    column_rows, index_rows, foreign_key_rows = fetch_schema_rows(dedicated_test_database)
    columns = group_columns(column_rows)
    indexes, uniqueness = group_indexes(index_rows)
    foreign_keys = group_foreign_keys(foreign_key_rows)

    assert len(contract) == 15
    assert set(contract).issubset(columns)

    for table_name, expected in contract.items():
        for column_name, expected_column in expected["columns"].items():
            assert columns[table_name][column_name] == expected_column
        assert indexes[table_name]["PRIMARY"] == expected["primary_key"]

        for index_name, expected_columns in expected["unique_indexes"].items():
            assert indexes[table_name][index_name] == expected_columns
            assert uniqueness[table_name][index_name]

        for index_name, expected_columns in expected["indexes"].items():
            assert indexes[table_name][index_name] == expected_columns

        actual_foreign_keys = list(foreign_keys[table_name].values())
        for expected_foreign_key in expected["foreign_keys"]:
            assert expected_foreign_key in actual_foreign_keys
