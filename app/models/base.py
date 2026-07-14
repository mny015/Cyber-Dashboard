"""Shared row conversion for plain dataclass models."""

from collections.abc import Mapping
from dataclasses import fields
from typing import ClassVar


class RowModel:
    """Convert dictionary cursor rows without adding persistence behavior."""

    __slots__ = ()

    TABLE_NAME: ClassVar[str]
    COLUMNS: ClassVar[tuple[str, ...]]

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        if not isinstance(row, Mapping):
            raise TypeError("Database rows must be mappings.")
        field_names = {field.name for field in fields(cls) if field.init}
        return cls(**{name: value for name, value in row.items() if name in field_names})

    @classmethod
    def from_rows(cls, rows):
        return [cls.from_row(row) for row in rows]


def as_bool(value):
    return bool(value)
