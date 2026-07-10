"""Transaction context manager for atomic synchronous MySQL operations."""

from contextlib import contextmanager

from pymysql.err import IntegrityError, MySQLError

from app.utils.database.connection import _lease
from app.utils.database.exceptions import (
    DatabaseIntegrityError,
    DatabaseQueryError,
    DatabaseTransactionError,
)


@contextmanager
def transaction(pool=None):
    """Yield a dictionary cursor, committing on success and rolling back on error."""
    with _lease(pool) as raw_connection:
        try:
            raw_connection.begin()
        except (MySQLError, OSError) as exc:
            raise DatabaseTransactionError() from exc

        cursor = None
        try:
            cursor = raw_connection.cursor()
            yield cursor
        except IntegrityError as exc:
            _rollback(raw_connection)
            raise DatabaseIntegrityError() from exc
        except (MySQLError, OSError) as exc:
            _rollback(raw_connection)
            raise DatabaseQueryError() from exc
        except BaseException:
            _rollback(raw_connection)
            raise
        else:
            try:
                raw_connection.commit()
            except (MySQLError, OSError) as exc:
                _rollback(raw_connection)
                raise DatabaseTransactionError() from exc
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except (MySQLError, OSError):
                    pass


def _rollback(raw_connection):
    try:
        raw_connection.rollback()
    except (MySQLError, OSError) as exc:
        raise DatabaseTransactionError() from exc
