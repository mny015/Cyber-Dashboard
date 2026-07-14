# Architecture Freeze Report

Date: 2026-07-14

Branch inspected: `test`

Baseline commit: `ecb8e47`

## Frozen Runtime Flow

```text
Browser -> Blueprint route mapping -> Controller -> Flask-WTF form
        -> Service (workflow only) or Repository (simple operation)
        -> Query builder or named runtime SQL
        -> Pooled PyMySQL connection / explicit transaction
        -> MySQL -> Plain dataclass model -> Controller -> Jinja -> Browser
```

The project uses synchronous PyMySQL only. It has no ORM, active-record persistence, async
database driver, or request-time schema initialization.

## Preserved Contracts

- 14 Blueprints and 72 application routes match `tests/contracts/route_contract.json`.
- Endpoint names, URL paths, HTTP methods, and authentication expectations remain frozen.
- All state-changing endpoints use POST-capable Flask-WTF forms, CSRF, authorization, and
  POST/Redirect/GET where a redirect is appropriate.
- The schema contract covers 19 application tables; `schema_migrations` is infrastructure metadata.
- All 28 foreign keys and their CASCADE, SET NULL, or RESTRICT rules remain documented and tested.
- SQL migrations `001` through `027` are the only authoritative schema history.
- User ownership is enforced in repository predicates, not only in presentation controls.
- Authentication, administrator authorization, MFA encryption, account lockout, audit preservation,
  upload inspection, safe redirects, security headers, and rate limiting remain active.

## Removed Obsolete Architecture

- Removed root `utils/` Python helpers after all callers moved under `app/utils/`.
- Removed `init_db.py`; numbered SQL migrations are authoritative.
- Replaced the obsolete root `create_admin.py` and `test_db.py` with import-safe scripts under
  `scripts/`.
- Removed duplicate export/catalog helpers and moved their maintained versions into `app/utils/`.
- Kept `scripts/legacy_data.py` because migration `018` uses it to preserve historical profile data.
- No Alembic runtime or migration tree remains; migration `025` only removes stale legacy metadata.

## Test and Tooling Gates

- Final local validation: 246 tests passed against dedicated MySQL test databases.
- Isolated validation without MySQL credentials: 191 passed and 55 explicitly skipped.
- Pytest imports modules without opening a database connection.
- Ordinary tests can run without MySQL; database tests skip unless `TEST_DB_NAME` is explicit.
- Integration tests reject unsafe database names and use dedicated names containing `test`.
- Clean-database migration tests verify all migrations apply once and never rerun.
- Existing-database migration tests clone a pre-018 schema, preserve fixture data, and verify the
  final schema and explain plans.
- GitHub Actions provisions MySQL 8.0 and runs migrations, seeds, compile checks, Ruff, Bandit,
  Radon, and the complete pytest suite.

## Complexity Baseline

Radon analyzed 555 functions, methods, and classes with average complexity A (2.28).

The bounded review hotspots are:

- `scripts/migrate.py:split_sql_statements`: D (23), a character-state SQL parser with parser tests.
- `app/utils/database/query_builder.py:QueryBuilder._compile_select`: C (16), the central validated
  SQL compiler with focused generation and injection-safety tests.
- `app/utils/uploads.py:detect_image_type`: C (11), signature detection covered by upload tests.

These are not candidates for broad restructuring after the freeze. Changes require a concrete defect,
focused tests, and preservation of the route and schema contracts.

## Change Policy

The backend architecture is frozen after this work. Continue with feature additions and targeted bug
fixes inside the established layers; do not reintroduce mixed route/controller modules, root database
helpers, Python schema DDL, ORM dependencies, or asynchronous database code.
