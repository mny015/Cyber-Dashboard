"""Compatibility entry point for migrating and seeding a local database."""

import sys

from scripts.migrate import run_migrations
from scripts.seed import seed_database


def main():
    print(
        "init_db.py is retained for compatibility. "
        "Use 'python scripts/migrate.py' and 'python scripts/seed.py' for explicit setup."
    )
    try:
        run_migrations()
        seed_database()
    except Exception as exc:
        print(f"[FAIL] Database initialization failed: {exc}", file=sys.stderr)
        if exc.__cause__:
            print(f"       {exc.__cause__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
