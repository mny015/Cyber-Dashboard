"""HTTP handlers for lab references and completion state."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import validate_action
from app.forms.labs import LabForm
from app.models import LabReference
from app.repositories import lab_repository, topic_repository
from app.utils.audit import log_audit
from app.utils.decorators import require_owned_record


@login_required
def index():
    platform_id = request.args.get("platform_id", type=int)
    return render_template(
        "labs/index.html",
        labs=lab_repository.list_visible(current_user.id, platform_id=platform_id),
        platforms=lab_repository.list_platforms(),
        selected_platform_id=platform_id,
    )


@login_required
def create():
    form, topics, platforms = _lab_form()
    if not form.validate_on_submit():
        return _render_form(None, form, topics, platforms)
    lab = lab_repository.create(_lab_model(form))
    log_audit("lab_created", f"Created lab {form.name.data}")
    flash("Lab added.", "success")
    return redirect(url_for("labs.detail", lab_id=lab.id))


@login_required
def detail(lab_id):
    return render_template("labs/detail.html", lab=_visible_lab_or_404(lab_id))


@login_required
def edit(lab_id):
    existing = _owned_lab_or_404(lab_id)
    form, topics, platforms = _lab_form(existing)
    if not form.validate_on_submit():
        return _render_form(existing, form, topics, platforms)
    lab_repository.update_owned(_lab_model(form, lab_id=lab_id), current_user.id)
    log_audit("lab_updated", f"Updated lab {form.name.data}")
    flash("Lab changes saved.", "success")
    return redirect(url_for("labs.detail", lab_id=lab_id))


@login_required
def delete(lab_id):
    if not validate_action():
        return redirect(url_for("labs.index"))
    lab = _owned_lab_or_404(lab_id)
    lab_repository.delete_owned(lab_id, current_user.id)
    log_audit("lab_deleted", f"Deleted lab {lab.name}")
    flash("Lab deleted.", "info")
    return redirect(url_for("labs.index"))


@login_required
def complete(lab_id):
    if not validate_action():
        return redirect(url_for("labs.detail", lab_id=lab_id))
    _visible_lab_or_404(lab_id)
    lab_repository.mark_completed_if_visible(lab_id, current_user.id)
    log_audit("lab_completed", f"Completed lab {lab_id}")
    flash("Lab marked as complete.", "success")
    return redirect(url_for("labs.detail", lab_id=lab_id))


@login_required
def incomplete(lab_id):
    if not validate_action():
        return redirect(url_for("labs.detail", lab_id=lab_id))
    _visible_lab_or_404(lab_id)
    lab_repository.mark_incomplete(lab_id, current_user.id)
    flash("Lab marked as incomplete.", "info")
    return redirect(url_for("labs.detail", lab_id=lab_id))


def _visible_lab_or_404(lab_id):
    return require_owned_record(lab_repository.find_visible(lab_id, current_user.id))


def _owned_lab_or_404(lab_id):
    return require_owned_record(lab_repository.find_owned(lab_id, current_user.id))


def _render_form(lab, form, topics, platforms):
    return render_template(
        "labs/form.html",
        lab=lab,
        form=form,
        topics=topics,
        platforms=platforms,
    )


def _lab_form(lab=None):
    topics = topic_repository.list_active(current_user.id)
    platforms = lab_repository.list_platforms()
    form = LabForm(obj=lab)
    form.platform_id.choices = [(platform.id, platform.name) for platform in platforms]
    form.topic_id.choices = [(None, "No topic")] + [
        (topic.id, topic.title) for topic in topics
    ]
    form.visibility.choices = [("personal", "Personal")]
    if current_user.is_admin:
        form.visibility.choices.append(("public", "Public"))
    if request.method == "GET" and not form.visibility.data:
        form.visibility.data = "personal"
    return form, topics, platforms


def _lab_model(form, lab_id=None):
    return LabReference(
        id=lab_id,
        name=form.name.data,
        platform_id=form.platform_id.data,
        url=form.url.data,
        notes=form.notes.data or "",
        topic_id=form.topic_id.data,
        owner_id=current_user.id,
        visibility=form.visibility.data,
    )
