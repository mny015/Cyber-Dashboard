"""Apply ordered plain-SQL migrations to the configured MySQL database."""

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pymysql
from pymysql.cursors import DictCursor

from config import get_config
from scripts.legacy_data import prepare_legacy_profile_images

DEFAULT_MIGRATIONS_DIR = PROJECT_ROOT / "migrations"
MIGRATION_PATTERN = re.compile(r"^(?P<version>\d{3})_[a-z0-9_]+\.sql$")
DATABASE_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
LEGACY_DATA_MIGRATION = "018_normalize_legacy_data.sql"


class MigrationError(RuntimeError):
    """Raised when migration discovery, history, or execution is unsafe."""


@dataclass(frozen=True)
class Migration:
    version: int
    filename: str
    path: Path
    sql: str
    checksum: str


@dataclass(frozen=True)
class MigrationResult:
    applied: tuple[str, ...]
    skipped: tuple[str, ...]


def discover_migrations(migrations_dir=DEFAULT_MIGRATIONS_DIR):
    directory = Path(migrations_dir)
    migrations = []
    seen_versions = set()

    for path in sorted(directory.glob("*.sql"), key=lambda item: item.name):
        match = MIGRATION_PATTERN.fullmatch(path.name)
        if not match:
            raise MigrationError(f"Invalid migration filename: {path.name}")
        version = int(match.group("version"))
        if version in seen_versions:
            raise MigrationError(f"Duplicate migration version: {version:03d}")
        seen_versions.add(version)
        sql = path.read_text(encoding="utf-8")
        migrations.append(
            Migration(
                version=version,
                filename=path.name,
                path=path,
                sql=sql,
                checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            )
        )

    if not migrations:
        raise MigrationError(f"No SQL migrations found in {directory}.")
    if migrations[0].filename != "001_create_schema_migrations.sql":
        raise MigrationError("The first migration must create schema_migrations.")
    return migrations


def split_sql_statements(sql):
    """Split SQL on semicolons while respecting strings and SQL comments."""
    statements = []
    buffer = []
    state = "normal"
    index = 0

    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if state == "line_comment":
            if char in "\r\n":
                buffer.append("\n")
                state = "normal"
            index += 1
            continue
        if state == "block_comment":
            if char == "*" and next_char == "/":
                state = "normal"
                index += 2
            else:
                index += 1
            continue
        if state in {"single", "double", "backtick"}:
            buffer.append(char)
            quote = {"single": "'", "double": '"', "backtick": "`"}[state]
            if char == "\\" and next_char:
                buffer.append(next_char)
                index += 2
                continue
            if char == quote:
                if next_char == quote:
                    buffer.append(next_char)
                    index += 2
                    continue
                state = "normal"
            index += 1
            continue

        if char == "-" and next_char == "-":
            state = "line_comment"
            index += 2
            continue
        if char == "#":
            state = "line_comment"
            index += 1
            continue
        if char == "/" and next_char == "*":
            state = "block_comment"
            index += 2
            continue
        if char in {"'", '"', "`"}:
            state = {"'": "single", '"': "double", "`": "backtick"}[char]
            buffer.append(char)
            index += 1
            continue
        if char == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            index += 1
            continue

        buffer.append(char)
        index += 1

    if state in {"single", "double", "backtick", "block_comment"}:
        raise MigrationError("Migration contains an unterminated string or comment.")
    statement = "".join(buffer).strip()
    if statement:
        statements.append(statement)
    return statements


def run_migrations(config=None, migrations_dir=DEFAULT_MIGRATIONS_DIR, output=print):
    config = config or get_config()
    migrations = discover_migrations(migrations_dir)
    ensure_database_exists(config)
    connection = database_connection(config)
    applied_now = []
    skipped = []

    try:
        ledger_created = _ensure_migration_ledger(connection, migrations[0], output)
        if ledger_created:
            applied_now.append(migrations[0].filename)
        applied_history = _load_applied_history(connection)
        _validate_history(applied_history, migrations)

        for migration in migrations:
            if migration.filename in applied_history:
                if ledger_created and migration.filename == migrations[0].filename:
                    continue
                output(f"[SKIP] {migration.filename}")
                skipped.append(migration.filename)
                continue
            output(f"[APPLY] {migration.filename}")
            _apply_migration(connection, migration, output)
            applied_now.append(migration.filename)
            output(f"[OK] {migration.filename}")
    finally:
        connection.close()

    output(
        f"Migration complete: {len(applied_now)} applied, "
        f"{len(skipped)} already current."
    )
    return MigrationResult(tuple(applied_now), tuple(skipped))


def ensure_database_exists(config):
    database_name = quote_database_identifier(config.DB_NAME)
    connection = server_connection(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {database_name} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        connection.close()


def quote_database_identifier(name):
    if not DATABASE_PATTERN.fullmatch(str(name)):
        raise MigrationError("DB_NAME may only contain letters, numbers, and underscores.")
    return f"`{name}`"


def server_connection(config):
    return pymysql.connect(**_connection_kwargs(config, include_database=False, autocommit=True))


def database_connection(config):
    return pymysql.connect(**_connection_kwargs(config, include_database=True, autocommit=False))


def _connection_kwargs(config, include_database, autocommit):
    kwargs = {
        "host": config.DB_HOST,
        "port": int(config.DB_PORT),
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "charset": config.DB_CHARSET,
        "autocommit": autocommit,
        "cursorclass": DictCursor,
    }
    if include_database:
        kwargs["database"] = config.DB_NAME
    return kwargs


def _ensure_migration_ledger(connection, first_migration, output):
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", ("schema_migrations",))
        ledger_exists = cursor.fetchone() is not None
    if not ledger_exists:
        output(f"[APPLY] {first_migration.filename}")
        _apply_migration(connection, first_migration, output)
        output(f"[OK] {first_migration.filename}")
        return True
    return False


def _load_applied_history(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT filename, checksum FROM schema_migrations ORDER BY filename")
        return {row["filename"]: row["checksum"] for row in cursor.fetchall()}


def _validate_history(applied_history, migrations):
    available = {migration.filename: migration for migration in migrations}
    missing_files = sorted(set(applied_history) - set(available))
    if missing_files:
        raise MigrationError(
            "Applied migration files are missing from the repository: " + ", ".join(missing_files)
        )
    for filename, checksum in applied_history.items():
        if available[filename].checksum != checksum:
            raise MigrationError(f"Applied migration was modified: {filename}")


def _apply_migration(connection, migration, output):
    try:
        connection.begin()
        if migration.filename == LEGACY_DATA_MIGRATION:
            prepare_legacy_profile_images(connection, PROJECT_ROOT, output)
        statements = split_sql_statements(migration.sql)
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            cursor.execute(
                """
                INSERT INTO schema_migrations (filename, checksum, applied_at)
                VALUES (%s, %s, NOW())
                """,
                (migration.filename, migration.checksum),
            )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        raise MigrationError(
            f"Migration failed: {migration.filename}. MySQL DDL can commit implicitly; "
            "the migration is idempotent and can be rerun after correcting the error."
        ) from exc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=DEFAULT_MIGRATIONS_DIR,
        help="Directory containing numbered SQL migrations.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        run_migrations(migrations_dir=args.migrations_dir)
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        cause = exc.__cause__
        if cause:
            print(f"       {cause}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
