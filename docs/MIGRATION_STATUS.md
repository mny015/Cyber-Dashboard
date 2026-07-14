# Final Layered Architecture Status

All registered routes map directly to plain controller functions. The full integration suite runs
against dedicated MySQL databases and includes clean and legacy-existing migration scenarios.

| Feature | Current registered module | Contract routes | Status |
|---|---|---:|---|
| Dashboard | `app/routes/dashboard.py` | 4 | Frozen |
| Authentication | `app/routes/auth.py` | 8 | Frozen |
| Administration | `app/routes/admin.py` | 12 | Frozen |
| Backup/export | `app/routes/backup.py` | 6 | Frozen |
| API | `app/routes/api.py` | 1 | Frozen |
| Categories | `app/routes/categories.py` | 4 | Frozen |
| Topics | `app/routes/topics.py` | 5 | Frozen |
| Contacts | `app/routes/contacts.py` | 4 | Frozen |
| Notes | `app/routes/notes.py` | 5 | Frozen |
| Labs | `app/routes/labs.py` | 7 | Frozen |
| Notifications | `app/routes/notifications.py` | 3 | Frozen |
| Profile | `app/routes/profile.py` | 2 | Frozen |
| Security findings | `app/routes/security.py` | 8 | Frozen |
| Scheduled tasks | `app/routes/scheduled_tasks.py` | 3 | Frozen |

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

## Freeze Rule

Major backend restructuring is complete. Future work must preserve the route and schema contracts,
keep controllers free of SQL, keep models persistence-free, and pass the static, unit, security,
and dedicated MySQL integration gates.
