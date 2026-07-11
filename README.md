# Cyber Dashboard

Cyber Dashboard is a Flask, Jinja, and MySQL web app for tracking cybersecurity learning work, lab practice, notes, findings, admin activity, and secure account management.

Repository: https://github.com/mny015/Cyber-Dashboard

## Overview

The app is built as a local coursework and portfolio project. It gives normal users a private workspace for topics, notes, labs, contacts, scheduled tasks, and security findings. Admin users get oversight tools for users, shared labs, requests, audit logs, platform metrics, and backup/export activity.

The project focuses on:

- Clear Flask app structure with blueprints.
- MySQL-backed CRUD features.
- Auth, roles, MFA, CSRF, rate limiting, and session hardening.
- Privacy-aware admin access.
- Audit evidence for important account, admin, lab, and CRUD actions.
- A responsive light/dark UI with theme-aware logos and favicons.

## Current Features

- User registration, login, logout, password changes, and protected routes.
- Admin role support with user management, ban/unban, delete, role updates, and password reset.
- MFA setup with TOTP and QR code generation.
- Topic management with categories, filters, detail pages, soft delete, and audit logs.
- Category CRUD with per-user ownership and audit logs.
- Contact CRUD with validation and audit logs.
- Private note editor with markdown-style preview, topic linking, soft delete, search, and audit logs.
- Admin note-access request workflow with user approval before private notes are visible.
- Lab reference manager for picoCTF, TryHackMe, Hack The Box, and other practice platforms.
- Shared admin labs that are visible to all users.
- Lab completion tracking.
- Scheduled task planner for users and admins.
- Security findings tracker with vulnerability and threat catalog support.
- Admin review for user-suggested vulnerabilities.
- Profile editing with validated database-backed profile images.
- Backup/export features for user and admin data.
- User dashboard with recent changes, room progress, scheduled work, and last-done activity.
- Admin dashboard with platform metrics, users, requests, audit logs, shared labs, and scheduled admin work.
- Light/dark theme toggle with saved browser preference.
- Theme-aware logo and favicon switching.
- Pytest test suite with fixtures for users, admins, auth, dashboards, CRUD audit logs, notes, labs, scheduled tasks, and security routes.

## Brand Assets

Logo and favicon files live in:

```text
app/static/image/
```

Current files:

- `logo-light.png`
- `logo-dark.png`
- `favicon-light.png`
- `favicon-dark.png`

The navbar and auth pages render both logo variants. CSS shows the light logo in light mode and the dark logo in dark mode. The favicon is linked in `app/templates/base.html` and switched by the existing theme JavaScript.

The old `image1.jpg` file was removed because it was not used by the app.

## Screenshots

No screenshot files are currently required for the app to run. If screenshots are added later, a suggested location is:

```text
docs/screenshots/
```

Suggested future screenshots:

- `login-light.png`
- `login-dark.png`
- `user-dashboard.png`
- `admin-dashboard.png`
- `notes.png`
- `labs.png`
- `scheduled-tasks.png`

## Tech Stack

- Python 3.13 or newer
- Flask 3
- Jinja2
- MySQL 8
- PyMySQL
- Flask-Login
- Flask-WTF and WTForms
- Werkzeug password hashing
- PyOTP and qrcode
- Flask-Talisman
- Flask-Limiter
- Plain CSS
- Vanilla JavaScript
- pytest and pytest-flask

## Project Structure

```text
Cyber Dashboard/
|-- app/
|   |-- __init__.py              # Flask app factory
|   |-- forms/                   # WTForms classes
|   |-- models/                  # User model and extension objects
|   |-- routes/                  # Blueprint route modules
|   |-- static/
|   |   |-- css/main.css
|   |   |-- js/main.js
|   |   |-- js/theme.js
|   |   `-- image/               # Logos and favicons
|   `-- templates/               # Jinja templates
|-- migrations/                  # Authoritative numbered SQL schema history
|-- scripts/
|   |-- migrate.py               # Plain-SQL migration runner
|   `-- seed.py                  # Reference catalog seed command
|-- tests/                       # pytest suite
|-- utils/                       # DB, audit, decorators, helpers, exports
|-- config.py                    # Environment-driven config
|-- create_admin.py              # Admin account helper
|-- init_db.py                   # Deprecated migrate-and-seed compatibility command
|-- run.py                       # Development server entry point
|-- test_db.py                   # DB connection smoke test
`-- requirements.txt
```

## Setup On Windows

Use PowerShell from the project root.

1. Clone the repository.

```powershell
git clone https://github.com/mny015/Cyber-Dashboard.git
cd "Cyber-Dashboard"
```

2. Create and activate a virtual environment.

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies.

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Use `requirements.txt`. Do not run `pip install -r requirements` because that file does not exist.

4. Create `.env`.

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your local values:

```env
SECRET_KEY=replace-with-a-long-random-secret-key
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=cyber_dashboard_user
DB_PASSWORD=replace-with-a-strong-database-password
DB_NAME=cyber_dashboard
DB_CHARSET=utf8mb4
DB_POOL_SIZE=5
DB_POOL_TIMEOUT=5
SESSION_COOKIE_SECURE=false
RATELIMIT_STORAGE_URI=memory://
LOG_FILE=instance/cyber_dashboard.log
```

The app intentionally requires environment variables. It does not use a fallback secret key or committed database password.

## Database Setup

Make sure MySQL is running, then apply the numbered schema migrations:

```powershell
python scripts/migrate.py
```

Apply reference seed data separately:

```powershell
python scripts/seed.py
```

`migrations/*.sql` is the single source of truth for schema history. The runner:

- Creates the configured database and `schema_migrations` ledger when missing.
- Applies SQL files once in filename order.
- Verifies SHA-256 checksums for already applied files.
- Upgrades clean databases and older project databases without deleting records.
- Normalizes known legacy columns and relationships through guarded SQL.
- Imports legacy profile image bytes before obsolete image columns are removed.

The application does not run migrations during requests. Alembic and ORM-based
migrations are not used. `init_db.py` is retained only as a compatibility command
that runs both the migration and seed steps:

```powershell
python init_db.py
```

Never edit a migration that has already been applied. Add the next numbered SQL
file instead. MySQL DDL can commit implicitly, so failed migrations are written
to be safely rerunnable after the reported data or permission issue is fixed.

Important tables include:

- `users`
- `profile_images`
- `topics`
- `categories`
- `contacts`
- `notes`
- `note_access_requests`
- `lab_platforms`
- `lab_references`
- `lab_completions`
- `scheduled_tasks`
- `security_findings`
- `vulnerability_catalog`
- `threat_catalog`
- `audit_logs`
- `work_logs`
- `roadmap_items`
- `progress_reflections`
- `activity_events`

The final schema contains 19 application tables plus the `schema_migrations`
ledger. The last four tables are retained from the existing database so older
coursework data remains available even though current routes do not use them.

Create or update an admin account:

```powershell
python create_admin.py
```

Check the database connection:

```powershell
python test_db.py
```

## Run The App

Activate the virtual environment first, then run:

```powershell
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

On Windows, prefer `python run.py` inside the active virtual environment. Avoid `python3 run.py` if it points to a different Python install.

## Test Commands

Run the full test suite:

```powershell
python -m pytest tests -v
```

Run focused tests:

```powershell
python -m pytest tests/test_auth_routes.py -v
python -m pytest tests/test_dashboard_routes.py -v
python -m pytest tests/test_page_rendering.py -v
python -m pytest tests/test_crud_audit_logs.py -v
python -m pytest tests/test_notes_routes.py -v
python -m pytest tests/test_lab_visibility.py -v
python -m pytest tests/test_scheduled_tasks.py -v
python -m pytest tests/test_security_routes.py -v
python -m pytest tests/test_migrations.py -v
```

Migration integration tests are destructive only to database names containing
`migration_test`. They load local credentials from `.env`, create isolated clean
and existing-copy databases, and remove those test databases afterward:

```powershell
$env:MIGRATION_TEST_DB_NAME="cyber_dashboard_migration_test"
$env:MIGRATION_EXISTING_SOURCE_DB_NAME="cyber_dashboard"
python -m pytest tests/test_migrations_integration.py -v -m integration
```

## Architecture Notes

- `app/__init__.py` creates the Flask app, loads config, initializes extensions, and registers routes.
- `app/routes/__init__.py` registers blueprints.
- Route modules own feature workflows.
- `utils/db.py` provides PyMySQL connection helpers and parameterized query execution.
- `app/utils/database/` provides pooled `connection()` and atomic `transaction()` context managers for repositories.
- `app/utils/database/query_builder.py` handles parameterized normal CRUD and filtering through strict identifier whitelists.
- `app/database/queries/` contains named `.sql` files only for complex runtime metrics, reports, and exports; `db.named_query()` loads them by validated name.
- `migrations/` remains the only location for numbered schema-changing SQL.
- `utils/audit.py` records audit log rows.
- `utils/decorators.py` contains role and login protection helpers.
- `utils/helpers.py` contains small formatting, slug, and validation helpers.
- `docs/DATABASE_RELATIONSHIPS.md` records the frozen foreign-key deletion and indexing policy.
- Templates extend `base.html`.
- Static CSS and JS are served locally from `app/static`.
- Tests use fixtures to create users, authenticate clients, and clean database records.

## Security Notes

- Passwords are stored with Werkzeug password hashes.
- Login uses Flask-Login.
- Sensitive forms use CSRF protection.
- Auth routes are rate limited.
- MFA uses TOTP.
- Session state includes `auth_version` so stale sessions can be invalidated after sensitive changes.
- SQL uses parameterized queries.
- Profile images are validated and stored in the database instead of being served from user-controlled static paths.
- Normal users can only manage their own topics, categories, notes, contacts, labs, tasks, and findings.
- Admins can see topic/category summaries and aggregate platform activity.
- Admins cannot read private note bodies unless the user approves a note-access request.
- Audit logs capture auth, admin, lab, scheduled task, backup/export, security finding, and core CRUD actions.

## Theme And Logo Behavior

- The default favicon is linked in `app/templates/base.html`.
- `app/static/js/theme.js` applies the stored or preferred theme early.
- `app/static/js/main.js` handles the theme toggle.
- `updateFavicon(theme)` switches between:
  - `/static/image/favicon-light.png`
  - `/static/image/favicon-dark.png`
- CSS switches between:
  - `logo-light.png`
  - `logo-dark.png`

Manual check:

1. Start the app with `python run.py`.
2. Open `/auth/login`.
3. Confirm the logo appears in the navbar and auth card.
4. Toggle light/dark mode.
5. Confirm the logo changes.
6. Check the browser tab favicon. Hard refresh if the browser cached the old icon.

## Development Workflow

Useful local workflow:

```powershell
git status
python scripts/migrate.py
python scripts/seed.py
python -m pytest tests -v
python run.py
```

Before committing:

```powershell
git status
git diff --check
python -m pytest tests -v
```

## Known Limitations

- Scheduled tasks are lightweight and do not yet support recurrence.
- Notifications currently focus on note-access requests.
- The roadmap feature is represented through existing topic, lab, task, and dashboard workflows.
- Screenshots and demo media are not committed yet.

## Future Improvements

- Add recurring scheduled tasks.
- Add a dedicated roadmap and milestone module.
- Add audit-log filters.
- Add dashboard screenshots and a short demo video under `docs/`.
- Add richer export/import restore flows.

## Repository

GitHub:

https://github.com/mny015/Cyber-Dashboard
