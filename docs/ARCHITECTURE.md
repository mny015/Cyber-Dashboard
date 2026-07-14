# Cyber Dashboard Architecture

This document defines the final layered structure. All registered feature routes map directly
to controller functions, and compatibility contracts protect the public route and database
surfaces from accidental changes.

## Request Flow

```text
Browser
  -> Routes
  -> Controllers
  -> Flask-WTF forms
  -> Services when business logic exists
  -> Repositories
  -> Query builder or named SQL
  -> Database connection and transaction layer
  -> MySQL
  -> Plain Python models
  -> Controllers
  -> Jinja templates
  -> Browser
```

No ORM or asynchronous database layer is part of this architecture.

## Responsibilities

### Routes

Route modules create Blueprints and declare URL paths, HTTP methods, endpoint names, and direct controller mappings. Migrated routes use `add_url_rule()` with the controller function as `view_func`. They do not contain request handling, SQL, business logic, or forwarding wrappers.

### Controllers

Controllers handle Flask request data, `current_user`, Flask-WTF forms, template rendering, flash messages, redirects, and calls to services or repositories. Controllers must not contain SQL after migration.

### Forms

Flask-WTF forms define server-side validation, normalization, field limits, and CSRF-backed submissions. Ownership and role authorization remain controller or service responsibilities rather than form responsibilities.

### Services

Services contain business workflows that coordinate multiple repositories or require transaction boundaries, such as authentication, note-access approval, user deletion, lab visibility, and exports. Simple CRUD does not require a service merely to satisfy the folder structure.

### Repositories

Repositories perform feature-specific persistence through the fluent query builder, named SQL reports, and explicit transaction blocks. They enforce ownership in lookup and mutation predicates, return plain models or clear aggregate dictionaries, and never read Flask request/session state or produce HTTP responses. Route and controller modules contain no runtime SQL.

### Models

Models are slotted dataclasses used only to represent persisted application data and explicit joined-row labels. Every application table is registered in `app.models.MODEL_REGISTRY`, and each model declares its table and known columns for safe row conversion and query validation. Models never open connections, execute SQL, save themselves, lazy-load relationships, or read Flask request/session state. They are not SQLAlchemy, ORM, or active-record models.

### Query Builder

The fluent query builder in `app/utils/database/query_builder.py` handles normal CRUD and filtering. It assembles identifiers only from the central table/column registry and keeps user values in PyMySQL parameters.

### Named SQL

Complex runtime reports and aggregates live as named `.sql` files directly under `app/database/queries/`. `db.named_query()` validates the query name, loads only from that directory, verifies named parameters, and executes through the pooled database layer. Simple CRUD does not belong in named SQL, and numbered schema migrations remain exclusively under `migrations/`.

### Database Layer

`app/utils/database/` owns the synchronous PyMySQL connection pool, dictionary
cursors, safe database exceptions, and transaction boundaries. Repositories use
two operation-level context managers:

```python
from app.utils.database import connection, transaction

with connection() as database:
    with database.cursor() as cursor:
        cursor.execute("SELECT * FROM topics WHERE owner_id = %s", (owner_id,))
        rows = cursor.fetchall()

with transaction() as cursor:
    cursor.execute("UPDATE topics SET status = %s WHERE id = %s", (status, topic_id))
```

`connection()` is for reads and always returns its connection to the pool.
`transaction()` commits on success and rolls back on failure. Driver exceptions
are converted to safe database-layer exceptions. There is no second root-level database helper;
scripts and tests use the same pooled infrastructure or an explicitly isolated migration connection.

### SQL Migrations

Numbered plain-SQL schema migrations in `migrations/` are the only authoritative schema history.
`scripts/migrate.py` applies them explicitly through PyMySQL; normal web requests never run
migrations. Seed data is handled separately by `scripts/seed.py`. The old `init_db.py` and Alembic
compatibility path have been removed, and no ORM is used.

## Architecture Freeze Gates

A feature is migrated only when all of the following remain unchanged:

1. Blueprint name, endpoint name, URL, and HTTP methods.
2. Authentication, authorization, ownership, CSRF, rate-limit, and audit behavior.
3. Templates, redirects, flash messages, database behavior, and privacy rules.
4. `tests/contracts/route_contract.json` and `tests/contracts/schema_contract.json`.
5. Existing and feature-specific tests.

The route and schema contracts, architecture tests, static analysis, and dedicated MySQL tests are
required gates. Major backend restructuring is frozen; future changes should be feature work or
targeted defect fixes within these established boundaries.
