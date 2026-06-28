import pymysql
from pymysql.cursors import DictCursor

from config import Config


def _connection_kwargs(overrides=None):
    overrides = overrides or {}
    kwargs = {
        "host": overrides.get("host", Config.DB_HOST),
        "user": overrides.get("user", Config.DB_USER),
        "password": overrides.get("password", Config.DB_PASSWORD),
        "database": overrides.get("database", Config.DB_NAME),
        "port": int(overrides.get("port", Config.DB_PORT)),
        "charset": overrides.get("charset", Config.DB_CHARSET),
        "autocommit": overrides.get("autocommit", False),
        "cursorclass": DictCursor,
    }
    if not kwargs["database"]:
        kwargs.pop("database")
    return kwargs


def get_connection(**overrides):
    connection = pymysql.connect(**_connection_kwargs(overrides))
    verify_connection(connection)
    return connection


def verify_connection(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def fetch_one(query, params=None, **overrides):
    connection = get_connection(**overrides)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    finally:
        connection.close()


def fetch_all(query, params=None, **overrides):
    connection = get_connection(**overrides)
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    finally:
        connection.close()


def fetch_scalar(query, params=None, default=None, **overrides):
    row = fetch_one(query, params=params, **overrides)
    if not row:
        return default
    return next(iter(row.values()))


def execute(query, params=None, commit=True, **overrides):
    connection = get_connection(**overrides)
    try:
        with connection.cursor() as cursor:
            affected = cursor.execute(query, params or ())
            lastrowid = cursor.lastrowid
        if commit:
            connection.commit()
        return affected, lastrowid
    except Exception:
        if commit:
            connection.rollback()
        raise
    finally:
        connection.close()