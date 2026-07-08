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
|-- migrations/versions/         # Historical Alembic migration history
|-- tests/                       # pytest suite
|-- utils/                       # DB, schema, audit, decorators, helpers, exports
|-- config.py                    # Environment-driven config
|-- create_admin.py              # Admin account helper
|-- init_db.py                   # Database initializer and seed script
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
SESSION_COOKIE_SECURE=false
RATELIMIT_STORAGE_URI=memory://
LOG_FILE=instance/cyber_dashboard.log
```

The app intentionally requires environment variables. It does not use a fallback secret key or committed database password.

## Database Setup

Make sure MySQL is running, then initialize the database:

```powershell
python init_db.py
```

The initializer can:

- Create the configured database if missing.
- Create required tables.
- Add missing columns for older local databases.
- Normalize profile images into the database.
- Seed lab platforms.
- Seed vulnerability and threat catalog entries.

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

## Database Schema Source Of Truth

The database schema lives in `utils/schema.py`. That module stores plain Python table metadata, `CREATE TABLE` statements, compatibility `ALTER TABLE` statements, table order, column names, keys, relationships, and whitelist helpers for safe dynamic SQL construction.

`init_db.py` imports schema data from `utils/schema.py` and executes it during local setup. The project does not use SQLAlchemy, Flask-SQLAlchemy, Peewee, Django ORM, or any ORM at runtime. Application queries still use PyMySQL and parameterized SQL through `utils/db.py`.

The `migrations/` folder is historical coursework migration history only. Current local setup uses `init_db.py` plus `utils/schema.py` as the source of truth.

A local-only DB map SQL file can be generated for ERD tools, but it is ignored by Git and is not part of the submitted source code.

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
```

Current suite size:

```text
55 tests
```

## Architecture Notes

- `app/__init__.py` creates the Flask app, loads config, initializes extensions, and registers routes.
- `app/routes/__init__.py` registers blueprints.
- Route modules own feature workflows.
- `utils/db.py` provides PyMySQL connection helpers and parameterized query execution.
- `utils/audit.py` records audit log rows.
- `utils/decorators.py` contains role and login protection helpers.
- `utils/helpers.py` contains small formatting, slug, and validation helpers.
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
python init_db.py
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
