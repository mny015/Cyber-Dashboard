# Layered Migration Status

The package boundaries now exist, but no feature has been migrated. Existing modules in `app/routes/` remain the registered production implementation.

| Feature | Current registered module | Contract routes | Status |
|---|---|---:|---|
| Dashboard | `app/routes/dashboard.py` | 4 | Not separated |
| Authentication | `app/routes/auth.py` | 7 | Not separated |
| Administration | `app/routes/admin.py` | 12 | Not separated |
| Backup/export | `app/routes/backup.py` | 5 | Not separated |
| API | `app/routes/api.py` | 1 | Not separated |
| Categories | `app/routes/categories.py` | 4 | Not separated |
| Topics | `app/routes/topics.py` | 5 | Not separated |
| Contacts | `app/routes/contacts.py` | 4 | Not separated |
| Notes | `app/routes/notes.py` | 5 | Not separated |
| Labs | `app/routes/labs.py` | 7 | Not separated |
| Notifications | `app/routes/notifications.py` | 3 | Not separated |
| Profile | `app/routes/profile.py` | 2 | Not separated |
| Security findings | `app/routes/security.py` | 8 | Not separated |
| Scheduled tasks | `app/routes/scheduled_tasks.py` | 3 | Not separated |

Total frozen application routes: **70**.

## Shared Infrastructure

| Area | Current state |
|---|---|
| Controllers | Package boundary created; no feature controller modules yet |
| Services | Package boundary created; no unnecessary service modules |
| Repositories | Package boundary created; no feature repositories yet |
| Plain models | Slotted dataclasses cover all 19 application tables; user loading moved to a repository |
| Database infrastructure | `app/utils/database/` exposes the existing helpers without changing callers |
| Named SQL | Loader and execution API active; user/admin dashboard metric aggregates migrated |
| Extensions | Centralized in `app/extensions.py`; `app.models` re-exports the same instances for compatibility |
| WSGI | `wsgi.py` provides a production-server entry point |
| Route compatibility | Frozen in `tests/contracts/route_contract.json` |
| Schema compatibility | Frozen in `tests/contracts/schema_contract.json` |

## Completion Rule

A row may be changed to **Migrated** only after direct `add_url_rule()` mappings point to real controller functions, controller SQL has moved to repositories or named queries, old and new Blueprints are not both registered, and route, security, schema, and feature tests pass without behavioral differences.
