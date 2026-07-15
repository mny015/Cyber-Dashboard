"""Focused accessibility checks for shared templates and key page controls."""

from pathlib import Path

from flask import Flask, flash, render_template_string
from jinja2 import FileSystemLoader
from werkzeug.datastructures import MultiDict

from app.forms.auth import LoginForm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"


def build_template_app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY="accessibility-test-secret", WTF_CSRF_ENABLED=False)
    app.jinja_loader = FileSystemLoader(TEMPLATES_DIR)
    app.jinja_env.globals["csrf_token"] = lambda: "accessibility-test-csrf-token"
    return app


def test_invalid_form_fields_reference_announced_errors_and_help_text():
    app = build_template_app()

    with app.test_request_context("/login", method="POST"):
        form = LoginForm(
            formdata=MultiDict({"email": "invalid", "password": ""}),
            meta={"csrf": False},
        )
        assert not form.validate()

        markup = render_template_string(
            """
            {% from "macros/forms.html" import form_field with context %}
            {{ form_field(form.email, help_text="Use the address linked to your account.") }}
            """,
            form=form,
        )

    assert '<label for="email">Email address</label>' in markup
    assert 'aria-invalid="true"' in markup
    assert 'aria-describedby="email-errors email-help"' in markup
    assert 'id="email-errors" role="alert" aria-live="assertive"' in markup
    assert 'id="email-help"' in markup


def test_flash_messages_use_appropriate_live_region_priority():
    app = build_template_app()

    with app.test_request_context("/"):
        flash("Changes saved.", "success")
        flash("Please correct the form.", "danger")
        markup = render_template_string(
            """
            {% from "macros/feedback.html" import flash_messages with context %}
            {{ flash_messages() }}
            """
        )

    assert 'role="status" aria-live="polite">Changes saved.' in markup
    assert 'role="alert" aria-live="assertive">Please correct the form.' in markup


def test_action_macro_outputs_valid_accessible_name_and_confirmation():
    app = build_template_app()

    with app.test_request_context("/"):
        markup = render_template_string(
            """
            {% from "macros/forms.html" import action_form with context %}
            {{ action_form(
                "/topics/7/delete",
                "Delete topic",
                confirm="Delete topic 'Web security'?",
                aria_label="Delete topic Web security"
            ) }}
            """
        )

    assert 'data-confirm="Delete topic' in markup
    assert 'aria-label="Delete topic Web security"' in markup
    assert "aria_label=" not in markup


def test_base_layout_provides_skip_navigation_and_named_controls():
    source = (TEMPLATES_DIR / "base.html").read_text(encoding="utf-8")

    assert 'class="skip-link" href="#main-content"' in source
    assert 'id="main-content" tabindex="-1"' in source
    assert 'aria-label="Open main navigation"' in source
    assert 'aria-label="Switch to dark theme"' in source
    assert 'aria-label="Main navigation"' in source


def test_data_tables_have_accessible_captions():
    table_templates = (
        "admin/audit_logs.html",
        "admin/category_summaries.html",
        "admin/note_requests.html",
        "admin/topic_summaries.html",
        "admin/users.html",
        "security/admin_vulnerabilities.html",
    )

    for relative_path in table_templates:
        source = (TEMPLATES_DIR / relative_path).read_text(encoding="utf-8")
        assert "data_table(" in source
        assert "caption=" in source


def test_filter_controls_have_explicit_labels_and_named_forms():
    expected_markup = {
        "topics/index.html": (
            'aria-label="Filter topics"',
            'for="topic-category-filter"',
            'id="topic-category-filter"',
        ),
        "labs/index.html": (
            'aria-label="Filter labs"',
            'for="lab-platform-filter"',
            'id="lab-platform-filter"',
        ),
        "notes/index.html": (
            'aria-label="Search and filter notes"',
            'for="note_search"',
            'for="topic_id"',
        ),
    }

    for relative_path, required_fragments in expected_markup.items():
        source = (TEMPLATES_DIR / relative_path).read_text(encoding="utf-8")
        for fragment in required_fragments:
            assert fragment in source


def test_keyboard_and_reduced_motion_rules_remain_present():
    javascript = (PROJECT_ROOT / "app" / "static" / "js" / "main.js").read_text(
        encoding="utf-8"
    )
    stylesheet = (PROJECT_ROOT / "app" / "static" / "css" / "main.css").read_text(
        encoding="utf-8"
    )

    assert 'event.key === "Escape"' in javascript
    assert "navToggle.focus()" in javascript
    assert "toggle.focus()" in javascript
    assert ":focus-visible" in stylesheet
    assert "prefers-reduced-motion: reduce" in stylesheet
    assert ".skip-link:focus" in stylesheet
