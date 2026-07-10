"""Safe exception types exposed by the database infrastructure layer."""


class DatabaseError(RuntimeError):
    """Base class for database failures safe to show outside the driver layer."""


class DatabaseConnectionError(DatabaseError):
    """Raised when a pooled MySQL connection cannot be obtained."""

    def __init__(self, message="The database connection is unavailable."):
        super().__init__(message)


class DatabaseQueryError(DatabaseError):
    """Raised when MySQL cannot execute a query."""

    def __init__(self, message="The database operation could not be completed."):
        super().__init__(message)


class DatabaseIntegrityError(DatabaseQueryError):
    """Raised when a query violates a database integrity constraint."""

    def __init__(self, message="The requested change conflicts with existing data."):
        super().__init__(message)


class DatabaseTransactionError(DatabaseError):
    """Raised when a transaction cannot begin, commit, or roll back safely."""

    def __init__(self, message="The database transaction could not be completed."):
        super().__init__(message)
