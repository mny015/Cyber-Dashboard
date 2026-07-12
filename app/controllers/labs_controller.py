"""HTTP handlers for lab references and completion state."""

from urllib.parse import urlparse

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import LabReference
from app.repositories import lab_repository, topic_repository
from utils.audit import log_audit
from utils.helpers import clean_text


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
    if request.method != "POST":
        return _render_form(None)
    values = _read_form()
    error = _validation_error(values)
    if error:
        flash(error, "danger")
        return _render_form(values)
    lab = lab_repository.create(_lab_model(values))
    log_audit("lab_created", f"Created lab {values['name']}")
    flash("Lab added successfully.", "success")
    return redirect(url_for("labs.detail", lab_id=lab.id))


@login_required
def detail(lab_id):
    return render_template("labs/detail.html", lab=_visible_lab_or_404(lab_id))


@login_required
def edit(lab_id):
    existing = _owned_lab_or_404(lab_id)
    if request.method != "POST":
        return _render_form(existing)
    values = _read_form()
    values["id"] = lab_id
    error = _validation_error(values)
    if error:
        flash(error, "danger")
        return _render_form(values)
    lab_repository.update_owned(_lab_model(values), current_user.id)
    log_audit("lab_updated", f"Updated lab {values['name']}")
    flash("Lab updated successfully.", "success")
    return redirect(url_for("labs.detail", lab_id=lab_id))


@login_required
def delete(lab_id):
    lab = _owned_lab_or_404(lab_id)
    lab_repository.delete_owned(lab_id, current_user.id)
    log_audit("lab_deleted", f"Deleted lab {lab.name}")
    flash("Lab deleted successfully.", "info")
    return redirect(url_for("labs.index"))


@login_required
def complete(lab_id):
    _visible_lab_or_404(lab_id)
    lab_repository.mark_completed_if_visible(lab_id, current_user.id)
    log_audit("lab_completed", f"Completed lab {lab_id}")
    flash("Lab marked complete.", "success")
    return redirect(url_for("labs.detail", lab_id=lab_id))


@login_required
def incomplete(lab_id):
    _visible_lab_or_404(lab_id)
    lab_repository.mark_incomplete(lab_id, current_user.id)
    flash("Lab marked incomplete.", "info")
    return redirect(url_for("labs.detail", lab_id=lab_id))


def _visible_lab_or_404(lab_id):
    lab = lab_repository.find_visible(lab_id, current_user.id)
    if not lab:
        abort(404)
    return lab


def _owned_lab_or_404(lab_id):
    lab = lab_repository.find_owned(lab_id, current_user.id)
    if not lab:
        abort(404)
    return lab


def _render_form(lab):
    return render_template(
        "labs/form.html",
        lab=lab,
        topics=topic_repository.list_active(current_user.id),
        platforms=lab_repository.list_platforms(),
    )


def _read_form():
    visibility = clean_text(request.form.get("visibility"))
    if not current_user.is_admin or visibility not in {"personal", "public"}:
        visibility = "personal"
    return {
        "name": clean_text(request.form.get("name")),
        "platform_id": request.form.get("platform_id", type=int),
        "url": clean_text(request.form.get("url")),
        "notes": clean_text(request.form.get("notes")),
        "topic_id": request.form.get("topic_id", type=int) or None,
        "visibility": visibility,
    }


def _validation_error(values):
    if not values["name"]:
        return "Lab name is required."
    if not lab_repository.platform_exists(values["platform_id"]):
        return "Choose a valid lab platform."
    parsed_url = urlparse(values["url"])
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return "Enter a valid HTTP or HTTPS lab URL."
    if values["topic_id"] and not topic_repository.exists_owned(
        values["topic_id"], current_user.id
    ):
        return "Choose one of your own topics."
    return None


def _lab_model(values):
    return LabReference(
        id=values.get("id"),
        name=values["name"],
        platform_id=values["platform_id"],
        url=values["url"],
        notes=values["notes"],
        topic_id=values["topic_id"],
        owner_id=current_user.id,
        visibility=values["visibility"],
    )
