# Layered Migration Status

All registered routes now map directly to plain controller functions. Database-backed integration tests remain intentionally pending when `TEST_DB_NAME` is not configured.

| Feature | Current registered module | Contract routes | Status |
|---|---|---:|---|
| Dashboard | `app/routes/dashboard.py` | 4 | Controller separated |
| Authentication | `app/routes/auth.py` | 8 | Controller separated |
| Administration | `app/routes/admin.py` | 12 | Controller separated |
| Backup/export | `app/routes/backup.py` | 6 | Controller separated |
| API | `app/routes/api.py` | 1 | Controller separated |
| Categories | `app/routes/categories.py` | 4 | Controller separated |
| Topics | `app/routes/topics.py` | 5 | Controller separated |
| Contacts | `app/routes/contacts.py` | 4 | Controller separated |
| Notes | `app/routes/notes.py` | 5 | Controller separated |
| Labs | `app/routes/labs.py` | 7 | Controller separated |
| Notifications | `app/routes/notifications.py` | 3 | Controller separated |
| Profile | `app/routes/profile.py` | 2 | Controller separated |
| Security findings | `app/routes/security.py` | 8 | Controller separated |
| Scheduled tasks | `app/routes/scheduled_tasks.py` | 3 | Controller separated |

Total frozen application routes: **72**. The additional routes serve a short-lived export ticket after a POST request and a recent identity-confirmation workflow for sensitive actions.

## Shared Infrastructure

| Area | Current state |
|---|---|
| Controllers | All 72 routes map directly to 14 plain controller modules through `add_url_rule()` |
| Services | Workflow services added for auth/MFA, audit, admin user management, notes, scheduled tasks, note-access notifications, security operations, and exports; simple reads remain repository-direct |
| Repositories | All application persistence migrated across 12 explicit feature repositories |
| Plain models | Slotted dataclasses cover all 19 application tables; user loading moved to a repository |
| Database infrastructure | Pooled query builder, named-query loader, and explicit transactions used by repositories |
| Named SQL | Complex lists, dashboards, audit reports, and privacy-aware exports migrated to named SQL |
| Extensions | Centralized exclusively in `app/extensions.py` |
| WSGI | `wsgi.py` provides a production-server entry point |
| Route compatibility | Frozen in `tests/contracts/route_contract.json` |
| Schema compatibility | Frozen in `tests/contracts/schema_contract.json` |

## Completion Rule

A row may be changed to **Migrated** only after direct `add_url_rule()` mappings point to real controller functions, controller SQL has moved to repositories or named queries, old and new Blueprints are not both registered, and route, security, schema, and feature tests pass without behavioral differences.
