"""Static contracts that prevent the retired architecture from returning."""

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCES = [
    path
    for root in (PROJECT_ROOT / "app", PROJECT_ROOT / "scripts")
    for path in root.rglob("*.py")
]


def imported_modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_legacy_root_architecture_is_absent():
    retired_paths = (
        PROJECT_ROOT / "init_db.py",
        PROJECT_ROOT / "create_admin.py",
        PROJECT_ROOT / "test_db.py",
    )

    assert all(not path.exists() for path in retired_paths)
    assert not list((PROJECT_ROOT / "utils").glob("*.py"))


def test_no_orm_or_async_database_architecture_is_present():
    forbidden_imports = {
        "sqlalchemy",
        "flask_sqlalchemy",
        "alembic",
        "peewee",
        "django",
        "aiomysql",
        "asyncmy",
    }

    for path in PYTHON_SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.AsyncFor, ast.AsyncWith))
            for node in ast.walk(tree)
        ), path
        roots = {module.split(".", 1)[0] for module in imported_modules(path)}
        assert roots.isdisjoint(forbidden_imports), path


def test_runtime_requirements_exclude_test_and_orm_packages():
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()

    for package in ("pytest", "ruff", "bandit", "radon", "sqlalchemy", "alembic"):
        assert package not in requirements


def test_application_has_no_debug_prints_or_python_schema_ddl():
    for path in (PROJECT_ROOT / "app").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            for node in ast.walk(tree)
        ), path
        assert "CREATE TABLE" not in source.upper(), path
        assert "ALTER TABLE" not in source.upper(), path
