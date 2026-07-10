import pymysql
import pytest
from pymysql.cursors import DictCursor

from app import create_app
from app.utils.database import (
    DatabaseConnectionError,
    DatabaseIntegrityError,
    DatabaseQueryError,
    DatabaseTransactionError,
    close_database,
    connection,
    transaction,
)
from app.utils.database.connection import MySQLConnectionPool, connection_settings


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
        self.commit_error = None
        self.rollback_error = None

    def ping(self, reconnect=False):
        if not self.open:
            raise pymysql.err.OperationalError(2006, "closed")

    def cursor(self):
        return self.cursor_instance

    def begin(self):
        self.begin_count += 1

    def commit(self):
        self.commit_count += 1
        if self.commit_error:
            raise self.commit_error

    def rollback(self):
        self.rollback_count += 1
        if self.rollback_error:
            raise self.rollback_error

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


def test_connection_settings_enable_dictionary_cursors():
    settings = connection_settings(
        {
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "3306",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "DB_NAME": "database",
            "DB_CHARSET": "utf8mb4",
        }
    )

    assert settings["cursorclass"] is DictCursor
    assert settings["autocommit"] is False


def test_successful_connection_is_reused_and_returned_to_pool():
    fake_connection = FakeConnection()
    pool = pool_for(fake_connection)

    with connection(pool) as first:
        assert first is fake_connection
        assert pool.leased_count == 1

    assert pool.leased_count == 0
    assert pool.available_count == 1
    assert pool.created_count == 1

    with connection(pool) as second:
        assert second is first

    assert pool.created_count == 1
    assert pool.available_count == 1


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


def test_query_exception_is_converted_without_raw_details():
    fake_connection = FakeConnection()
    pool = pool_for(fake_connection)

    with pytest.raises(DatabaseQueryError) as raised:
        with connection(pool):
            raise pymysql.err.OperationalError(1054, "private column details")

    assert "private column details" not in str(raised.value)
    assert pool.available_count == 1


def test_commit_failure_becomes_transaction_failure():
    fake_connection = FakeConnection()
    fake_connection.commit_error = pymysql.err.OperationalError(2013, "private commit details")
    pool = pool_for(fake_connection)

    with pytest.raises(DatabaseTransactionError) as raised:
        with transaction(pool):
            pass

    assert "private commit details" not in str(raised.value)
    assert fake_connection.rollback_count >= 1


def test_rollback_failure_becomes_transaction_failure_and_discards_connection():
    fake_connection = FakeConnection()
    fake_connection.rollback_error = pymysql.err.OperationalError(2013, "private rollback details")
    pool = pool_for(fake_connection)

    with pytest.raises(DatabaseTransactionError) as raised:
        with transaction(pool):
            raise ValueError("trigger rollback")

    assert "private rollback details" not in str(raised.value)
    assert fake_connection.close_count == 1
    assert pool.created_count == 0


def test_pool_close_closes_idle_connections():
    fake_connection = FakeConnection()
    pool = pool_for(fake_connection)
    with connection(pool):
        pass

    pool.close()

    assert fake_connection.close_count == 1
    assert pool.created_count == 0
    with pytest.raises(DatabaseConnectionError):
        pool.acquire()


def test_app_factory_registers_a_lazy_pool():
    app = create_app("testing")
    pool = app.extensions["mysql_connection_pool"]

    assert pool.created_count == 0
    close_database(app)


@pytest.mark.integration
def test_real_mysql_connection_returns_dictionary_rows(dedicated_test_database):
    app = create_app("testing")
    try:
        with app.app_context():
            pool = app.extensions["mysql_connection_pool"]
            with connection() as raw_connection:
                with raw_connection.cursor() as cursor:
                    cursor.execute("SELECT DATABASE() AS database_name, 1 AS connected")
                    row = cursor.fetchone()

            assert row == {"database_name": dedicated_test_database, "connected": 1}
            assert pool.available_count == 1
            assert pool.leased_count == 0
    finally:
        close_database(app)
