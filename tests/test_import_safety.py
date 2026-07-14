"""Importing application and test modules must never open a database connection."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_module_imports_do_not_connect_to_mysql():
    script = textwrap.dedent(
        """
        import importlib
        import pkgutil
        import pymysql

        def reject_connection(*args, **kwargs):
            raise AssertionError("Database connection attempted during module import")

        pymysql.connect = reject_connection

        for package_name in ("app", "scripts", "tests"):
            package = importlib.import_module(package_name)
            for module in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
                importlib.import_module(module.name)
        """
    )
    environment = os.environ.copy()
    environment.update(
        {
            "APP_ENV": "testing",
            "SECRET_KEY": "import-safety-test-secret",
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "3306",
            "DB_USER": "import_test_user",
            "DB_PASSWORD": "import-test-password",
            "DB_NAME": "import_safety_test",
            "DB_CHARSET": "utf8mb4",
            "RATELIMIT_STORAGE_URI": "memory://",
        }
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
