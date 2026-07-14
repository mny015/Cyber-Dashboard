"""Focused server-side validation tests for state-changing forms."""

from werkzeug.datastructures import MultiDict

from app.forms.admin import AdminPasswordResetForm, RoleForm
from app.forms.auth import MfaTokenForm, RegisterForm
from app.forms.categories import CategoryForm
from app.forms.contacts import ContactForm
from app.forms.labs import LabForm
from app.forms.scheduled_tasks import ScheduledTaskForm


def build_form(app, form_class, values):
    with app.test_request_context("/", method="POST"):
        return form_class(formdata=MultiDict(values), meta={"csrf": False})


def test_registration_requires_valid_email_and_matching_strong_password(app):
    form = build_form(
        app,
        RegisterForm,
        {
            "display_name": "Student",
            "email": "not-an-email",
            "password": "short",
            "confirm_password": "different",
        },
    )

    assert not form.validate()
    assert form.email.errors
    assert form.password.errors
    assert form.confirm_password.errors


def test_category_and_contact_validation_rejects_malformed_values(app):
    category = build_form(
        app,
        CategoryForm,
        {"name": "Networking", "description": "", "color": "blue"},
    )
    contact = build_form(
        app,
        ContactForm,
        {
            "name": "Contact",
            "email": "invalid",
            "phone": "javascript:alert(1)",
            "notes": "",
        },
    )

    assert not category.validate()
    assert category.color.errors == ["Enter a six-digit hexadecimal color."]
    assert not contact.validate()
    assert contact.email.errors
    assert contact.phone.errors == ["Enter a valid phone number."]


def test_select_fields_reject_values_outside_controller_supplied_choices(app):
    lab = build_form(
        app,
        LabForm,
        {
            "name": "Practice lab",
            "platform_id": "999",
            "url": "https://example.com/lab",
            "topic_id": "",
            "visibility": "public",
        },
    )
    lab.platform_id.choices = [(1, "picoCTF")]
    lab.topic_id.choices = [(None, "No topic")]
    lab.visibility.choices = [("personal", "Personal")]

    task = build_form(
        app,
        ScheduledTaskForm,
        {"title": "Review", "task_type": "unknown", "scope": "private"},
    )
    task.task_type.choices = [("review", "Review")]
    task.scope.choices = [("personal", "Personal")]

    assert not lab.validate()
    assert lab.platform_id.errors
    assert lab.visibility.errors
    assert not task.validate()
    assert task.task_type.errors
    assert task.scope.errors


def test_mfa_role_and_admin_password_forms_enforce_contracts(app):
    mfa_form = build_form(app, MfaTokenForm, {"token": "123"})
    role_form = build_form(app, RoleForm, {"role": "owner"})
    password_form = build_form(
        app,
        AdminPasswordResetForm,
        {"password": "NewPassword123!", "confirm_password": "Mismatch123!"},
    )

    assert not mfa_form.validate()
    assert not role_form.validate()
    assert not password_form.validate()
    assert password_form.confirm_password.errors == ["Passwords must match."]
