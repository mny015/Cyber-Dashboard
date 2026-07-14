"""Small normalization and validation functions shared by Flask-WTF forms."""

import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^[0-9+\-\s()]{7,20}$")


def clean_text(value):
    return (value or "").strip()


def normalize_email(value):
    return clean_text(value).lower()


def slugify(value):
    normalized = clean_text(value).lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def is_valid_email(value):
    return bool(EMAIL_PATTERN.fullmatch(clean_text(value)))


def is_valid_phone(value):
    return bool(PHONE_PATTERN.fullmatch(clean_text(value)))
