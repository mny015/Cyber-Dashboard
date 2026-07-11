"""Public database API for repositories and services."""

from app.utils.database.connection import close_database, connection, init_database
from app.utils.database.exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseIntegrityError,
    DatabaseQueryError,
    DatabaseTransactionError,
)
from app.utils.database.query_builder import (
    Database,
    InvalidIdentifierError,
    InvalidOperatorError,
    PaginationResult,
    QueryBuilderError,
    UnsafeQueryError,
    WriteResult,
    db,
)
from app.utils.database.transaction import transaction


__all__ = [
    "DatabaseConnectionError",
    "DatabaseError",
    "DatabaseIntegrityError",
    "DatabaseQueryError",
    "DatabaseTransactionError",
    "Database",
    "InvalidIdentifierError",
    "InvalidOperatorError",
    "PaginationResult",
    "QueryBuilderError",
    "UnsafeQueryError",
    "WriteResult",
    "close_database",
    "connection",
    "db",
    "init_database",
    "transaction",
]
