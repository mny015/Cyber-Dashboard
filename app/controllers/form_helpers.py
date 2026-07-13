"""Small HTTP helpers shared by form-handling controllers."""

from flask import flash

from app.forms.common import ActionForm, error_messages


def flash_form_errors(form, fallback="The submitted form is invalid."):
    messages = error_messages(form)
    for message in messages or [fallback]:
        flash(message, "danger")


def validate_action(fallback="The requested action could not be validated."):
    form = ActionForm()
    if form.validate_on_submit():
        return True
    flash_form_errors(form, fallback)
    return False
