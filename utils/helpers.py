import re
from datetime import date, datetime


def slugify(value):
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def format_date(value, fallback="Not set"):
    if not value:
        return fallback
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def is_valid_email(value):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value or ""))


def is_valid_phone(value):
    return bool(re.match(r"^[0-9+\-\s()]{7,20}$", value or ""))


def clean_text(value):
    return (value or "").strip()
