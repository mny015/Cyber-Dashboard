"""Shared forms and validation helpers for state-changing actions."""

from flask_wtf import FlaskForm
from wtforms import SubmitField


class ActionForm(FlaskForm):
    """CSRF-protected form for actions that require no additional data."""

    submit = SubmitField("Confirm")


def optional_int(value):
    """Coerce an optional select value without hiding malformed input."""

    if value in (None, ""):
        return None
    return int(value)


def error_messages(form):
    """Return human-readable validation errors in field order."""

    return [message for messages in form.errors.values() for message in messages]
