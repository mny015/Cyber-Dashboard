"""Strict date parsing and display helpers."""

from datetime import date, datetime


DATETIME_INPUT_FORMATS = ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S")


def parse_datetime(value, formats=DATETIME_INPUT_FORMATS):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).strip())
    except ValueError:
        pass
    for candidate_format in formats:
        try:
            return datetime.strptime(str(value).strip(), candidate_format)
        except ValueError:
            continue
    raise ValueError("Date and time must use a supported format.")


def format_date(value, fallback="Not set"):
    if not value:
        return fallback
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)
