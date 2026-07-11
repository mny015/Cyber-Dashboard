"""Readable synchronous query builder for parameterized application SQL."""

import re
from dataclasses import dataclass
from math import ceil
from typing import Mapping

from app.utils.database.connection import connection
from app.utils.database.exceptions import NamedQueryError
from app.utils.database.named_queries import load_named_query, prepare_named_parameters
from app.utils.database.transaction import transaction


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
WHERE_OPERATORS = {"=", "!=", "<>", "<", "<=", ">", ">=", "LIKE", "NOT LIKE"}
JOIN_OPERATORS = {"=", "!=", "<>", "<", "<=", ">", ">="}
ORDER_DIRECTIONS = {"ASC", "DESC"}

# This is runtime query metadata only. Numbered SQL migrations remain the schema
# source of truth. Explicit columns keep request data out of SQL identifiers.
TABLE_COLUMNS = {
    "users": frozenset(
        {
            "id", "email", "password_hash", "display_name", "role", "is_banned",
            "mfa_secret", "mfa_enabled", "auth_version", "failed_login_count",
            "last_failed_login_at", "locked_until", "profile_bio", "profile_image",
            "created_at", "updated_at",
        }
    ),
    "profile_images": frozenset(
        {"image_hash", "image_data", "mime_type", "byte_size", "created_at"}
    ),
    "categories": frozenset(
        {"id", "name", "description", "color", "is_deleted", "owner_id", "created_at", "updated_at"}
    ),
    "contacts": frozenset(
        {"id", "name", "email", "phone", "notes", "is_deleted", "owner_id", "created_at", "updated_at"}
    ),
    "topics": frozenset(
        {
            "id", "title", "slug", "description", "status", "priority", "notes",
            "is_deleted", "category_id", "owner_id", "created_at", "updated_at",
        }
    ),
    "audit_logs": frozenset({"id", "action", "details", "ip_address", "user_id", "created_at"}),
    "notes": frozenset(
        {"id", "title", "body", "topic_id", "owner_id", "is_deleted", "created_at", "updated_at"}
    ),
    "note_access_requests": frozenset(
        {
            "id", "topic_id", "note_id", "requester_admin_id", "status",
            "requested_at", "responded_at",
        }
    ),
    "lab_platforms": frozenset({"id", "name", "slug"}),
    "lab_references": frozenset(
        {
            "id", "name", "platform_id", "url", "notes", "topic_id", "owner_id",
            "visibility", "is_deleted", "created_at", "updated_at",
        }
    ),
    "lab_completions": frozenset({"id", "lab_id", "user_id", "completed_at"}),
    "vulnerability_catalog": frozenset(
        {
            "id", "code", "name", "category", "default_severity", "description",
            "source", "approval_status", "is_active", "created_by_user_id",
            "reviewed_by_user_id", "reviewed_at", "created_at", "updated_at",
        }
    ),
    "threat_catalog": frozenset(
        {"id", "code", "name", "default_level", "description", "source", "is_active", "created_at", "updated_at"}
    ),
    "security_findings": frozenset(
        {
            "id", "owner_id", "vulnerability_id", "threat_id", "activity_type",
            "title", "target", "severity", "status", "evidence", "notes",
            "detected_at", "is_deleted", "created_at", "updated_at",
        }
    ),
    "scheduled_tasks": frozenset(
        {
            "id", "user_id", "created_by", "title", "description", "task_type",
            "due_at", "status", "scope", "created_at", "updated_at",
        }
    ),
    "work_logs": frozenset(
        {
            "id", "title", "log_type", "content", "evidence_url", "risk_rating",
            "log_date", "owner_id", "created_at", "updated_at",
        }
    ),
    "roadmap_items": frozenset(
        {"id", "title", "milestone", "status", "due_date", "topic_id", "owner_id", "created_at", "updated_at"}
    ),
    "progress_reflections": frozenset(
        {"id", "insight", "challenge", "next_step", "owner_id", "created_at", "updated_at"}
    ),
    "activity_events": frozenset(
        {"id", "event_type", "intensity", "occurred_on", "owner_id", "created_at", "updated_at"}
    ),
}


class QueryBuilderError(ValueError):
    """Base class for rejected query-builder input."""


class InvalidIdentifierError(QueryBuilderError):
    """Raised when a table or column is outside the explicit schema registry."""


class InvalidOperatorError(QueryBuilderError):
    """Raised when an operator or ordering direction is not whitelisted."""


class UnsafeQueryError(QueryBuilderError):
    """Raised when a write could affect every row unintentionally."""


@dataclass(frozen=True)
class WriteResult:
    affected_rows: int
    last_insert_id: int | None = None


@dataclass(frozen=True)
class PaginationResult:
    items: list[dict]
    total: int
    page: int
    per_page: int
    pages: int

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def has_previous(self):
        return self.page > 1


@dataclass(frozen=True)
class Predicate:
    connector: str
    kind: str
    column: str
    operator: str | None = None
    value: object = None


@dataclass(frozen=True)
class JoinClause:
    join_type: str
    table: str
    left_column: str
    operator: str
    right_column: str


class Database:
    """Execution facade used by the fluent builder."""

    def table(self, table_name):
        return QueryBuilder(self, table_name)

    def named_query(self, query_name, parameters=None, *, fetch="all"):
        """Execute a trusted complex SELECT loaded from app/database/queries."""
        sql = load_named_query(query_name)
        bound_parameters = prepare_named_parameters(sql, parameters)
        if fetch == "all":
            return self._fetch_all(sql, bound_parameters)
        if fetch == "one":
            return self._fetch_one(sql, bound_parameters)
        raise NamedQueryError("Named query fetch mode must be 'all' or 'one'.")

    def _fetch_all(self, sql, params):
        with connection() as raw_connection:
            with raw_connection.cursor() as cursor:
                cursor.execute(sql, params)
                return list(cursor.fetchall())

    def _fetch_one(self, sql, params):
        with connection() as raw_connection:
            with raw_connection.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()

    def _execute(self, sql, params):
        with transaction() as cursor:
            cursor.execute(sql, params)
            return WriteResult(cursor.rowcount, cursor.lastrowid or None)

    def _executemany(self, sql, params):
        with transaction() as cursor:
            cursor.executemany(sql, params)
            return WriteResult(cursor.rowcount, cursor.lastrowid or None)


class QueryBuilder:
    """Mutable fluent query definition with immediate, explicit execution methods."""

    def __init__(self, database, table_name):
        self._database = database
        self._table = validate_table(table_name)
        self._select_columns = ["*"]
        self._predicates = []
        self._joins = []
        self._group_columns = []
        self._having_predicates = []
        self._order_clauses = []
        self._limit = None
        self._offset = None

    def select(self, *columns):
        normalized = normalize_columns(columns) or ["*"]
        self._select_columns = normalized
        return self

    def where(self, column, operator, value):
        self._predicates.append(
            Predicate("AND", "basic", column, normalize_operator(operator, WHERE_OPERATORS), value)
        )
        return self

    def or_where(self, column, operator, value):
        self._predicates.append(
            Predicate("OR", "basic", column, normalize_operator(operator, WHERE_OPERATORS), value)
        )
        return self

    def where_in(self, column, values):
        if isinstance(values, (str, bytes)):
            raise QueryBuilderError("where_in values must be a collection.")
        normalized_values = tuple(values)
        if not normalized_values:
            raise QueryBuilderError("where_in requires at least one value.")
        self._predicates.append(Predicate("AND", "in", column, value=normalized_values))
        return self

    def where_null(self, column):
        self._predicates.append(Predicate("AND", "null", column))
        return self

    def where_not_null(self, column):
        self._predicates.append(Predicate("AND", "not_null", column))
        return self

    def join(self, table_name, left_column, operator, right_column):
        return self._add_join("INNER", table_name, left_column, operator, right_column)

    def left_join(self, table_name, left_column, operator, right_column):
        return self._add_join("LEFT", table_name, left_column, operator, right_column)

    def group_by(self, *columns):
        self._group_columns.extend(normalize_columns(columns))
        return self

    def having(self, column, operator, value):
        self._having_predicates.append(
            Predicate("AND", "basic", column, normalize_operator(operator, WHERE_OPERATORS), value)
        )
        return self

    def order_by(self, column, direction="ASC"):
        normalized_direction = str(direction).strip().upper()
        if normalized_direction not in ORDER_DIRECTIONS:
            raise InvalidOperatorError("Order direction must be ASC or DESC.")
        self._order_clauses.append((column, normalized_direction))
        return self

    def limit(self, value):
        self._limit = validate_non_negative_integer(value, "limit")
        return self

    def offset(self, value):
        self._offset = validate_non_negative_integer(value, "offset")
        return self

    def all(self):
        sql, params = self._compile_select()
        return self._database._fetch_all(sql, params)

    def first(self):
        query = self._clone()
        query._limit = 1
        sql, params = query._compile_select()
        return self._database._fetch_one(sql, params)

    def count(self):
        inner_sql, params = self._compile_select(
            trusted_select_sql="1", include_order=False, include_pagination=False
        )
        sql = f"SELECT COUNT(*) AS `aggregate` FROM ({inner_sql}) AS `count_query`"
        row = self._database._fetch_one(sql, params)
        return int(row["aggregate"] if row else 0)

    def exists(self):
        sql, params = self._compile_select(
            trusted_select_sql="1 AS `exists_value`",
            include_order=False,
            include_pagination=False,
        )
        sql = f"{sql} LIMIT %s"
        row = self._database._fetch_one(sql, (*params, 1))
        return row is not None

    def insert(self, values):
        self._ensure_insert_shape()
        columns, row_values = self._validate_values(values)
        column_sql = ", ".join(self._quote_column(column) for column in columns)
        placeholders = ", ".join("%s" for _column in columns)
        sql = f"INSERT INTO {quote_table(self._table)} ({column_sql}) VALUES ({placeholders})"
        return self._database._execute(sql, tuple(row_values))

    def insert_many(self, rows):
        self._ensure_insert_shape()
        normalized_rows = list(rows)
        if not normalized_rows:
            raise QueryBuilderError("insert_many requires at least one row.")
        columns, first_values = self._validate_values(normalized_rows[0])
        parameter_rows = [tuple(first_values)]
        expected_columns = set(columns)
        for row in normalized_rows[1:]:
            if not isinstance(row, Mapping) or set(row) != expected_columns:
                raise QueryBuilderError("Every inserted row must use the same columns.")
            parameter_rows.append(tuple(row[column] for column in columns))

        column_sql = ", ".join(self._quote_column(column) for column in columns)
        placeholders = ", ".join("%s" for _column in columns)
        sql = f"INSERT INTO {quote_table(self._table)} ({column_sql}) VALUES ({placeholders})"
        return self._database._executemany(sql, tuple(parameter_rows))

    def update(self, values):
        if not self._predicates:
            raise UnsafeQueryError("UPDATE requires at least one WHERE condition.")
        self._ensure_simple_write_shape()
        columns, row_values = self._validate_values(values)
        assignments = ", ".join(f"{self._quote_column(column)} = %s" for column in columns)
        where_sql, where_params = self._compile_predicates(self._predicates)
        sql = f"UPDATE {quote_table(self._table)} SET {assignments} WHERE {where_sql}"
        return self._database._execute(sql, (*row_values, *where_params))

    def delete(self):
        if not self._predicates:
            raise UnsafeQueryError("DELETE requires at least one WHERE condition.")
        self._ensure_simple_write_shape()
        where_sql, params = self._compile_predicates(self._predicates)
        sql = f"DELETE FROM {quote_table(self._table)} WHERE {where_sql}"
        return self._database._execute(sql, params)

    def paginate(self, page=1, per_page=20):
        page = validate_positive_integer(page, "page")
        per_page = validate_positive_integer(per_page, "per_page")
        total = self.count()
        query = self._clone()
        query._limit = per_page
        query._offset = (page - 1) * per_page
        items = query.all()
        return PaginationResult(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=ceil(total / per_page) if total else 0,
        )

    def _add_join(self, join_type, table_name, left_column, operator, right_column):
        joined_table = validate_table(table_name)
        normalized_operator = normalize_operator(operator, JOIN_OPERATORS)
        allowed_tables = self._allowed_tables | {joined_table}
        self._quote_column(left_column, allowed_tables=allowed_tables)
        self._quote_column(right_column, allowed_tables=allowed_tables)
        clause = JoinClause(join_type, joined_table, left_column, normalized_operator, right_column)
        self._joins.append(clause)
        return self

    def _compile_select(
        self,
        trusted_select_sql=None,
        include_order=True,
        include_pagination=True,
    ):
        params = []
        select_sql = trusted_select_sql or ", ".join(
            self._quote_column(column, allow_wildcard=True) for column in self._select_columns
        )
        parts = [f"SELECT {select_sql} FROM {quote_table(self._table)}"]

        for clause in self._joins:
            parts.append(
                f"{clause.join_type} JOIN {quote_table(clause.table)} ON "
                f"{self._quote_column(clause.left_column)} {clause.operator} "
                f"{self._quote_column(clause.right_column)}"
            )

        if self._predicates:
            predicate_sql, predicate_params = self._compile_predicates(self._predicates)
            parts.append(f"WHERE {predicate_sql}")
            params.extend(predicate_params)
        if self._group_columns:
            parts.append("GROUP BY " + ", ".join(self._quote_column(column) for column in self._group_columns))
        if self._having_predicates:
            having_sql, having_params = self._compile_predicates(self._having_predicates)
            parts.append(f"HAVING {having_sql}")
            params.extend(having_params)
        if include_order and self._order_clauses:
            order_sql = ", ".join(
                f"{self._quote_column(column)} {direction}"
                for column, direction in self._order_clauses
            )
            parts.append(f"ORDER BY {order_sql}")
        if include_pagination:
            if self._offset is not None and self._limit is None:
                raise QueryBuilderError("offset requires limit.")
            if self._limit is not None:
                parts.append("LIMIT %s")
                params.append(self._limit)
            if self._offset is not None:
                parts.append("OFFSET %s")
                params.append(self._offset)

        return " ".join(parts), tuple(params)

    def _compile_predicates(self, predicates):
        sql_parts = []
        params = []
        for index, predicate in enumerate(predicates):
            prefix = "" if index == 0 else f" {predicate.connector} "
            column_sql = self._quote_column(predicate.column)
            if predicate.kind == "basic":
                sql_parts.append(f"{prefix}{column_sql} {predicate.operator} %s")
                params.append(predicate.value)
            elif predicate.kind == "in":
                placeholders = ", ".join("%s" for _value in predicate.value)
                sql_parts.append(f"{prefix}{column_sql} IN ({placeholders})")
                params.extend(predicate.value)
            elif predicate.kind == "null":
                sql_parts.append(f"{prefix}{column_sql} IS NULL")
            elif predicate.kind == "not_null":
                sql_parts.append(f"{prefix}{column_sql} IS NOT NULL")
        return "".join(sql_parts), tuple(params)

    def _quote_column(self, column, allow_wildcard=False, allowed_tables=None):
        if not isinstance(column, str):
            raise InvalidIdentifierError("Column names must be strings.")
        available_tables = allowed_tables or self._allowed_tables
        pieces = column.split(".")
        if len(pieces) == 1:
            table_name = self._table
            column_name = pieces[0]
            prefix = ""
        elif len(pieces) == 2:
            table_name, column_name = pieces
            if table_name not in available_tables:
                raise InvalidIdentifierError("Qualified column uses an unavailable table.")
            prefix = f"{quote_table(table_name)}."
        else:
            raise InvalidIdentifierError("Column names may contain one optional table qualifier.")

        if column_name == "*" and allow_wildcard:
            return f"{prefix}*"
        validate_column(table_name, column_name)
        return f"{prefix}`{column_name}`"

    @property
    def _allowed_tables(self):
        return {self._table} | {join.table for join in self._joins}

    def _validate_values(self, values):
        if not isinstance(values, Mapping) or not values:
            raise QueryBuilderError("Write values must be a non-empty mapping.")
        columns = list(values)
        for column in columns:
            validate_column(self._table, column)
        return columns, [values[column] for column in columns]

    def _ensure_insert_shape(self):
        if any(
            (
                self._predicates,
                self._joins,
                self._group_columns,
                self._having_predicates,
                self._order_clauses,
                self._limit is not None,
                self._offset is not None,
            )
        ):
            raise QueryBuilderError("INSERT cannot include SELECT query clauses.")

    def _ensure_simple_write_shape(self):
        if any(
            (
                self._joins,
                self._group_columns,
                self._having_predicates,
                self._order_clauses,
                self._limit is not None,
                self._offset is not None,
            )
        ):
            raise QueryBuilderError("UPDATE and DELETE support WHERE conditions only.")

    def _clone(self):
        clone = QueryBuilder(self._database, self._table)
        clone._select_columns = list(self._select_columns)
        clone._predicates = list(self._predicates)
        clone._joins = list(self._joins)
        clone._group_columns = list(self._group_columns)
        clone._having_predicates = list(self._having_predicates)
        clone._order_clauses = list(self._order_clauses)
        clone._limit = self._limit
        clone._offset = self._offset
        return clone


def validate_table(table_name):
    if not isinstance(table_name, str) or not IDENTIFIER_PATTERN.fullmatch(table_name):
        raise InvalidIdentifierError("Invalid table identifier.")
    if table_name not in TABLE_COLUMNS:
        raise InvalidIdentifierError("Table is not available to the query builder.")
    return table_name


def validate_column(table_name, column_name):
    if not isinstance(column_name, str) or not IDENTIFIER_PATTERN.fullmatch(column_name):
        raise InvalidIdentifierError("Invalid column identifier.")
    if column_name not in TABLE_COLUMNS[table_name]:
        raise InvalidIdentifierError("Column is not available for this table.")
    return column_name


def quote_table(table_name):
    return f"`{validate_table(table_name)}`"


def normalize_operator(operator, allowed_operators):
    normalized = str(operator).strip().upper()
    if normalized not in allowed_operators:
        raise InvalidOperatorError("SQL operator is not allowed.")
    return normalized


def normalize_columns(columns):
    if len(columns) == 1 and isinstance(columns[0], (list, tuple)):
        return list(columns[0])
    return list(columns)


def validate_non_negative_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise QueryBuilderError(f"{name} must be a non-negative integer.")
    return value


def validate_positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise QueryBuilderError(f"{name} must be a positive integer.")
    return value


db = Database()


__all__ = [
    "Database",
    "InvalidIdentifierError",
    "InvalidOperatorError",
    "PaginationResult",
    "QueryBuilderError",
    "UnsafeQueryError",
    "WriteResult",
    "db",
]
