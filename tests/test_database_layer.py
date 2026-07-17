import pymysql
import pytest
from pymysql.cursors import DictCursor

from app.utils.database import (
    DatabaseConnectionError,
    DatabaseIntegrityError,
    connection,
    transaction,
)
from app.utils.database.connection import MySQLConnectionPool

TEST_SETTINGS = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "test-user",
    "password": "test-password",
    "database": "test_database",
    "charset": "utf8mb4",
    "autocommit": False,
    "cursorclass": DictCursor,
}


class FakeCursor:
    def __init__(self):
        self.closed = False
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))
        return 1

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.open = True
        self.cursor_instance = FakeCursor()
        self.begin_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def ping(self, reconnect=False):
        if not self.open:
            raise pymysql.err.OperationalError(2006, "closed")

    def cursor(self):
        return self.cursor_instance

    def begin(self):
        self.begin_count += 1

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.close_count += 1
        self.open = False


def pool_for(fake_connection):
    return MySQLConnectionPool(
        TEST_SETTINGS,
        max_size=1,
        timeout=0.01,
        connect_factory=lambda **_kwargs: fake_connection,
    )


def test_successful_connection_is_reused_and_returned_to_pool():
    fake_connection = FakeConnection()
    pool = pool_for(fake_connection)

    with connection(pool) as first:
        assert first is fake_connection
        assert pool.leased_count == 1

    with connection(pool) as second:
        assert second is first

    assert pool.leased_count == 0
    assert pool.available_count == 1
    assert pool.created_count == 1


def test_failed_connection_is_converted_without_raw_driver_details():
    def fail_connection(**_kwargs):
        raise pymysql.err.OperationalError(2003, "private-host-and-password")

    pool = MySQLConnectionPool(TEST_SETTINGS, max_size=1, connect_factory=fail_connection)

    with pytest.raises(DatabaseConnectionError) as raised:
        pool.acquire()

    assert "private-host-and-password" not in str(raised.value)
    assert pool.created_count == 0


def test_transaction_commits_and_returns_connection():
    fake_connection = FakeConnection()
    pool = pool_for(fake_connection)

    with transaction(pool) as cursor:
        cursor.execute("UPDATE example SET value = %s", (1,))

    assert fake_connection.begin_count == 1
    assert fake_connection.commit_count == 1
    assert pool.available_count == 1
    assert pool.leased_count == 0


def test_transaction_rolls_back_on_application_exception():
    fake_connection = FakeConnection()
    pool = pool_for(fake_connection)

    with pytest.raises(ValueError, match="stop transaction"):
        with transaction(pool):
            raise ValueError("stop transaction")

    assert fake_connection.commit_count == 0
    assert fake_connection.rollback_count >= 1
    assert pool.available_count == 1


def test_integrity_exception_is_converted_and_connection_is_returned():
    fake_connection = FakeConnection()
    pool = pool_for(fake_connection)

    with pytest.raises(DatabaseIntegrityError) as raised:
        with transaction(pool):
            raise pymysql.err.IntegrityError(1062, "private duplicate details")

    assert "private duplicate details" not in str(raised.value)
    assert fake_connection.rollback_count >= 1
    assert pool.available_count == 1
