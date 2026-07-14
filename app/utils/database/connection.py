"""Small synchronous PyMySQL connection pool with Flask-managed configuration."""

from contextlib import contextmanager
from queue import Empty, Full, LifoQueue
from threading import Lock

import pymysql
from flask import current_app, has_app_context
from pymysql.cursors import DictCursor
from pymysql.err import IntegrityError, MySQLError

from app.utils.database.exceptions import (
    DatabaseConnectionError,
    DatabaseIntegrityError,
    DatabaseQueryError,
)

DEFAULT_POOL_SIZE = 5
DEFAULT_POOL_TIMEOUT = 5.0
POOL_EXTENSION_KEY = "mysql_connection_pool"


class MySQLConnectionPool:
    """Bounded, thread-safe pool that owns every connection it creates."""

    def __init__(
        self,
        settings,
        max_size=DEFAULT_POOL_SIZE,
        timeout=DEFAULT_POOL_TIMEOUT,
        connect_factory=pymysql.connect,
    ):
        if int(max_size) < 1:
            raise ValueError("max_size must be at least 1")
        self._settings = dict(settings)
        self._max_size = int(max_size)
        self._timeout = float(timeout)
        self._connect_factory = connect_factory
        self._available = LifoQueue(maxsize=self._max_size)
        self._lock = Lock()
        self._created_count = 0
        self._leased_ids = set()
        self._closed = False

    @classmethod
    def from_config(cls, config, connect_factory=pymysql.connect):
        settings = connection_settings(config)
        return cls(
            settings,
            max_size=config.get("DB_POOL_SIZE", DEFAULT_POOL_SIZE),
            timeout=config.get("DB_POOL_TIMEOUT", DEFAULT_POOL_TIMEOUT),
            connect_factory=connect_factory,
        )

    @property
    def created_count(self):
        return self._created_count

    @property
    def available_count(self):
        return self._available.qsize()

    @property
    def leased_count(self):
        with self._lock:
            return len(self._leased_ids)

    def acquire(self):
        """Borrow a healthy connection, waiting briefly when the pool is busy."""
        while True:
            if self._closed:
                raise DatabaseConnectionError("The database connection pool is closed.")

            try:
                raw_connection = self._available.get_nowait()
            except Empty:
                raw_connection = self._create_or_wait()

            if self._is_healthy(raw_connection):
                with self._lock:
                    self._leased_ids.add(id(raw_connection))
                return raw_connection
            self._discard(raw_connection)

    def release(self, raw_connection):
        """Reset and return a borrowed connection, or discard it if unhealthy."""
        with self._lock:
            was_leased = id(raw_connection) in self._leased_ids
            self._leased_ids.discard(id(raw_connection))
            pool_closed = self._closed
        if not was_leased:
            return

        try:
            raw_connection.rollback()
        except (MySQLError, OSError):
            self._discard(raw_connection)
            return

        if pool_closed or not self._is_healthy(raw_connection):
            self._discard(raw_connection)
            return

        try:
            self._available.put_nowait(raw_connection)
        except Full:
            self._discard(raw_connection)

    def close(self):
        """Close idle connections; leased connections close when returned."""
        with self._lock:
            self._closed = True
        while True:
            try:
                raw_connection = self._available.get_nowait()
            except Empty:
                break
            self._discard(raw_connection)

    def _create_or_wait(self):
        reserved_slot = False
        with self._lock:
            if self._created_count < self._max_size:
                self._created_count += 1
                reserved_slot = True

        if reserved_slot:
            try:
                return self._connect_factory(**self._settings)
            except (MySQLError, OSError) as exc:
                with self._lock:
                    self._created_count -= 1
                raise DatabaseConnectionError() from exc

        try:
            return self._available.get(timeout=self._timeout)
        except Empty as exc:
            raise DatabaseConnectionError("The database connection pool is busy.") from exc

    def _is_healthy(self, raw_connection):
        try:
            if not getattr(raw_connection, "open", True):
                return False
            raw_connection.ping(reconnect=False)
            return True
        except (MySQLError, OSError):
            return False

    def _discard(self, raw_connection):
        try:
            raw_connection.close()
        finally:
            with self._lock:
                if self._created_count:
                    self._created_count -= 1


def connection_settings(config):
    """Build validated PyMySQL keyword arguments from Flask configuration."""
    required_names = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [name for name in required_names if not str(config.get(name, "")).strip()]
    if missing:
        raise DatabaseConnectionError("Database configuration is incomplete.")
    try:
        port = int(config["DB_PORT"])
    except (TypeError, ValueError) as exc:
        raise DatabaseConnectionError("Database configuration is invalid.") from exc

    return {
        "host": config["DB_HOST"],
        "port": port,
        "user": config["DB_USER"],
        "password": config["DB_PASSWORD"],
        "database": config["DB_NAME"],
        "charset": config.get("DB_CHARSET", "utf8mb4"),
        "autocommit": False,
        "cursorclass": DictCursor,
    }


def init_database(app):
    """Register one lazy connection pool on a Flask application."""
    if POOL_EXTENSION_KEY not in app.extensions:
        app.extensions[POOL_EXTENSION_KEY] = MySQLConnectionPool.from_config(app.config)


def get_pool():
    if not has_app_context():
        raise DatabaseConnectionError("Database access requires an application context.")
    pool = current_app.extensions.get(POOL_EXTENSION_KEY)
    if pool is None:
        raise DatabaseConnectionError("The database connection pool is not initialized.")
    return pool


def close_database(app=None):
    """Close a registered pool during an explicit application shutdown or test."""
    target_app = app or (current_app._get_current_object() if has_app_context() else None)
    if target_app is None:
        return
    pool = target_app.extensions.pop(POOL_EXTENSION_KEY, None)
    if pool is not None:
        pool.close()


@contextmanager
def _lease(pool=None):
    managed_pool = pool or get_pool()
    raw_connection = managed_pool.acquire()
    try:
        yield raw_connection
    finally:
        managed_pool.release(raw_connection)


@contextmanager
def connection(pool=None):
    """Borrow a pooled connection for read operations and always return it."""
    with _lease(pool) as raw_connection:
        try:
            yield raw_connection
        except IntegrityError as exc:
            raise DatabaseIntegrityError() from exc
        except (MySQLError, OSError) as exc:
            raise DatabaseQueryError() from exc
