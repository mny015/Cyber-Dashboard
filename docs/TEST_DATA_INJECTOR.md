# Test Data Injector

`docs/inject_test_data.py` creates a coherent demo workspace for manual testing.
It is not run by Flask, migrations, or automated tests.

## What It Creates

- One administrator and three normal users with form-valid demo email addresses.
- Eight categories, twelve topics, and twelve correlated Markdown notes.
- Nineteen labs from official TryHackMe, Hack The Box Academy, picoCTF, and
  PortSwigger pages.
- Admin-owned public labs and user-owned personal labs.
- Thirteen lab completions, scheduled work, reflections, work logs, and activity events.
- Eleven realistic but entirely synthetic security findings against reserved `.test`
  targets.
- Pending and approved note-access requests.
- A pending vulnerability suggestion for the administrator review screen.
- Audit entries suitable for dashboard and audit-log testing.

Categories own related topics. Each topic has a note, and each lab is linked to the
same topic while its description identifies the related note. This preserves the
application's actual schema, which links labs and notes through `topic_id`.

## Safety

The injector:

- Refuses to run with `APP_ENV=production`.
- Refuses MySQL system databases.
- Requires `--confirm-db` to exactly match `DB_NAME`.
- Uses the existing pooled PyMySQL transaction layer and parameterized query builder.
- Hashes the demo password using the application's password helper.
- Makes no schema changes.
- Never deletes non-demo users.

## Run It

Apply migrations first:

```powershell
python scripts/migrate.py
```

Validate without writing:

```powershell
python docs/inject_test_data.py --confirm-db cyber_dashboard --dry-run
```

Insert the dataset:

```powershell
python docs/inject_test_data.py --confirm-db cyber_dashboard
```

Refresh an existing copy of the fixed demo dataset:

```powershell
python docs/inject_test_data.py --confirm-db cyber_dashboard --replace
```

`--replace` also removes the earlier injector accounts that used the rejected
`@cyberdashboard.test` email format before creating the corrected accounts.

By default, the injector generates one strong password for all four demo accounts
and prints it after a successful insertion. To choose the shared password yourself,
run:

```powershell
python docs/inject_test_data.py --confirm-db cyber_dashboard `
  --password "AnotherStrongPassword!"
```

The generated or supplied password is hashed before it is stored.

## Demo Accounts

| Role | Email |
| --- | --- |
| Administrator | `admin.demo@demo.cyberdashboard.dev` |
| User | `maya.patel@demo.cyberdashboard.dev` |
| User | `jordan.lee@demo.cyberdashboard.dev` |
| User | `samira.khan@demo.cyberdashboard.dev` |

All people, organizations, findings, contacts, IP addresses, and `.test` targets in
the dataset are synthetic. Lab names and links point to official training-platform
pages.
