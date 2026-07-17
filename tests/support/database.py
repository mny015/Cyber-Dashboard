"""Database adapter used only by dedicated application-flow test fixtures."""

from contextlib import contextmanager

from app.utils.database import connection, transaction


class TestDatabase:
    """Run test setup and assertions through the configured application pool."""

    __test__ = False

    def __init__(self, application, database_name):
        self.application = application
        self.database_name = database_name

    @contextmanager
    def connect(self):
        with self.application.app_context():
            with connection() as raw_connection:
                yield raw_connection

    def fetch_one(self, query, parameters=None):
        with self.connect() as raw_connection:
            with raw_connection.cursor() as cursor:
                cursor.execute(query, parameters or ())
                return cursor.fetchone()

    def fetch_all(self, query, parameters=None):
        with self.connect() as raw_connection:
            with raw_connection.cursor() as cursor:
                cursor.execute(query, parameters or ())
                return list(cursor.fetchall())

    def execute(self, query, parameters=None):
        with self.application.app_context():
            with transaction() as cursor:
                affected_rows = cursor.execute(query, parameters or ())
                return affected_rows, cursor.lastrowid or None

    def scalar(self, query, parameters=None, default=None):
        row = self.fetch_one(query, parameters)
        return next(iter(row.values())) if row else default

    def assert_connected_to_test_database(self):
        connected_name = self.scalar("SELECT DATABASE() AS database_name")
        if connected_name != self.database_name:
            raise AssertionError(
                f"Expected test database {self.database_name!r}, got {connected_name!r}."
            )
