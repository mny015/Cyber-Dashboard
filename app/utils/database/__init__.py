"""Public database API for repositories and services."""

from app.utils.database.connection import close_database, connection, init_database
from app.utils.database.exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseIntegrityError,
    DatabaseQueryError,
    DatabaseTransactionError,
    InvalidNamedQueryNameError,
    NamedQueryError,
    NamedQueryNotFoundError,
    NamedQueryParameterError,
)
from app.utils.database.named_queries import clear_named_query_cache, load_named_query
from app.utils.database.query_builder import (
    CursorDatabase,
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
    "CursorDatabase",
    "InvalidIdentifierError",
    "InvalidNamedQueryNameError",
    "InvalidOperatorError",
    "NamedQueryError",
    "NamedQueryNotFoundError",
    "NamedQueryParameterError",
    "PaginationResult",
    "QueryBuilderError",
    "UnsafeQueryError",
    "WriteResult",
    "close_database",
    "clear_named_query_cache",
    "connection",
    "db",
    "init_database",
    "load_named_query",
    "transaction",
]
