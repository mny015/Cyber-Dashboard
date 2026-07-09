# Cyber Dashboard Architecture

This document defines the intended layered structure. The current feature modules remain in `app/routes/` until each feature is migrated and its compatibility tests pass.

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

Repositories perform feature-specific persistence through parameterized SQL. They return plain rows or plain Python models and do not read Flask request or session state.

### Models

Models are plain Python objects or dataclasses used to represent application data. They are not SQLAlchemy, ORM, or active-record models.

### Query Builder

The future query builder belongs in `app/utils/database/`. It may assemble optional SQL clauses only from strict server-owned whitelists. User values always remain database parameters.

### Named SQL

Complex runtime queries belong in feature modules under `app/database/queries/`. Named SQL modules contain query definitions only; execution and transactions stay in `app/utils/database/`.

### SQL Migrations

Numbered schema migrations belong in `migrations/`. During scaffolding, `init_db.py` remains the active setup path and the historical migration files remain untouched. Migration ownership must be resolved without introducing an ORM dependency.

## Compatibility Gates

A feature is migrated only when all of the following remain unchanged:

1. Blueprint name, endpoint name, URL, and HTTP methods.
2. Authentication, authorization, ownership, CSRF, rate-limit, and audit behavior.
3. Templates, redirects, flash messages, database behavior, and privacy rules.
4. `tests/contracts/route_contract.json` and `tests/contracts/schema_contract.json`.
5. Existing and feature-specific tests.

Old and new Blueprints must never be registered simultaneously.
