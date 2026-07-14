"""Load trusted complex runtime SQL by validated name."""

import re
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path

from app.utils.database.exceptions import (
    InvalidNamedQueryNameError,
    NamedQueryError,
    NamedQueryNotFoundError,
    NamedQueryParameterError,
)

QUERY_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PARAMETER_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
NAMED_PLACEHOLDER_PATTERN = re.compile(r"%\(([A-Za-z_][A-Za-z0-9_]*)\)s")
POSITIONAL_PLACEHOLDER_PATTERN = re.compile(r"(?<!%)%s")
QUERY_DIRECTORY = Path(__file__).resolve().parents[2] / "database" / "queries"


def load_named_query(query_name):
    """Return one cached UTF-8 SQL file from the fixed runtime-query directory."""
    validated_name = validate_query_name(query_name)
    query_directory = QUERY_DIRECTORY.resolve()
    return _read_named_query(validated_name, str(query_directory))


def prepare_named_parameters(sql, parameters=None):
    """Validate mapping keys and require an exact placeholder match."""
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, Mapping):
        raise NamedQueryParameterError("Named query parameters must be a mapping.")

    normalized = dict(parameters)
    if any(
        not isinstance(name, str) or not PARAMETER_NAME_PATTERN.fullmatch(name)
        for name in normalized
    ):
        raise NamedQueryParameterError("Named query parameter names are invalid.")
    if POSITIONAL_PLACEHOLDER_PATTERN.search(sql):
        raise NamedQueryParameterError("Named SQL files must use named placeholders.")

    required_names = set(NAMED_PLACEHOLDER_PATTERN.findall(sql))
    supplied_names = set(normalized)
    missing_names = required_names - supplied_names
    unexpected_names = supplied_names - required_names
    if missing_names:
        raise NamedQueryParameterError(
            "Missing named query parameters: " + ", ".join(sorted(missing_names))
        )
    if unexpected_names:
        raise NamedQueryParameterError(
            "Unexpected named query parameters: " + ", ".join(sorted(unexpected_names))
        )
    return normalized


def validate_query_name(query_name):
    if not isinstance(query_name, str) or not QUERY_NAME_PATTERN.fullmatch(query_name):
        raise InvalidNamedQueryNameError()
    return query_name


def clear_named_query_cache():
    """Clear cached SQL after controlled test or development file changes."""
    _read_named_query.cache_clear()


def named_query_cache_info():
    return _read_named_query.cache_info()


@lru_cache(maxsize=128)
def _read_named_query(query_name, query_directory_text):
    query_directory = Path(query_directory_text)
    query_path = (query_directory / f"{query_name}.sql").resolve()

    # This also rejects symlinks whose target resolves outside the fixed folder.
    if query_path.parent != query_directory or query_path.suffix != ".sql":
        raise InvalidNamedQueryNameError()
    if not query_path.is_file():
        raise NamedQueryNotFoundError()

    try:
        query = query_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise NamedQueryError("The named query file could not be read.") from exc
    if not query:
        raise NamedQueryError("The named query file is empty.")
    return query


__all__ = [
    "clear_named_query_cache",
    "load_named_query",
    "named_query_cache_info",
    "prepare_named_parameters",
    "validate_query_name",
]
