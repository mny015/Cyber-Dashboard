# Numbered SQL Migrations

This directory is the single authoritative schema history for Cyber Dashboard.
The application uses PyMySQL and plain SQL; Alembic, SQLAlchemy, and other ORMs
are not part of the migration path.

The history creates 19 application tables and the `schema_migrations` ledger.
Four historical data tables found in the existing database are retained even
though they are not currently accessed by Flask routes.

## Rules

- Migration files use `NNN_description.sql` names and run in filename order.
- Applied filenames and SHA-256 checksums are stored in `schema_migrations`.
- Never edit an applied migration. Add the next numbered file instead.
- Every migration must be safe to rerun after a partial MySQL DDL failure.
- Runtime query SQL does not belong in this directory.
- Catalog and reference seeds are maintained by `scripts/seed.py`.
- Migrations are run explicitly and never during a Flask web request.

Foreign-key deletion behavior is frozen by migration `026`; relationship and
index decisions are documented in `docs/DATABASE_RELATIONSHIPS.md`. Migration
`027` adds the composite indexes used by dashboard and list query paths.
Migration `028` expands `users.mfa_secret` so encrypted TOTP secrets fit
without truncation.

## Commands

```powershell
python scripts/migrate.py
python scripts/seed.py
```

`python init_db.py` remains as a deprecated compatibility command that runs both
steps. New setup and deployment instructions should use the explicit commands.

## Existing Databases

The create migrations use `CREATE TABLE IF NOT EXISTS`. Later compatibility
migrations add columns that older project versions may lack, normalize lab and
note-access data, and restore required indexes and foreign keys. Before the
legacy profile columns are removed, the runner imports valid image bytes from
the old database columns or the historical static upload directory.

MySQL can commit DDL statements implicitly, so a failed migration may leave part
of its DDL applied even after rollback. The SQL files guard compatibility
changes and can be rerun after the underlying data or permission problem is
fixed. A migration is recorded only after all of its statements succeed.
