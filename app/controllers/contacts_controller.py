"""HTTP handlers for user-owned contacts."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.contact import Contact
from app.repositories import contact_repository
from utils.audit import log_audit
from utils.helpers import clean_text, is_valid_email, is_valid_phone


def _get_contact_or_404(contact_id):
    contact = contact_repository.find_owned(contact_id, current_user.id)
    if not contact:
        abort(404)
    return contact


@login_required
def index():
    return render_template(
        "contacts/index.html",
        contacts=contact_repository.list_for_user(current_user.id),
    )


@login_required
def create():
    contact = Contact(owner_id=current_user.id)
    if request.method != "POST":
        return render_template("contacts/form.html", contact=None)

    _apply_form(contact)
    if not _is_valid(contact):
        return render_template("contacts/form.html", contact=contact)

    contact_repository.create(contact)
    log_audit("contact_created", f"Created contact {contact.id}")
    flash("Contact created successfully.", "success")
    return redirect(url_for("contacts.index"))


@login_required
def edit(contact_id):
    contact = _get_contact_or_404(contact_id)
    if request.method != "POST":
        return render_template("contacts/form.html", contact=contact)

    _apply_form(contact)
    if not _is_valid(contact):
        return render_template("contacts/form.html", contact=contact)

    contact_repository.update_owned(contact, current_user.id)
    log_audit("contact_updated", f"Updated contact {contact.id}")
    flash("Contact updated successfully.", "success")
    return redirect(url_for("contacts.index"))


@login_required
def delete(contact_id):
    contact = _get_contact_or_404(contact_id)
    contact_repository.delete_owned(contact.id, current_user.id)
    log_audit("contact_deleted", f"Deleted contact {contact.id}")
    flash("Contact deleted successfully.", "info")
    return redirect(url_for("contacts.index"))


def _apply_form(contact):
    contact.name = clean_text(request.form.get("name"))
    contact.email = clean_text(request.form.get("email"))
    contact.phone = clean_text(request.form.get("phone"))
    contact.notes = clean_text(request.form.get("notes"))


def _is_valid(contact):
    if not contact.name:
        flash("Contact name is required.", "danger")
        return False
    if not is_valid_email(contact.email):
        flash("Enter a valid email address.", "danger")
        return False
    if not is_valid_phone(contact.phone):
        flash("Enter a valid phone number.", "danger")
        return False
    return True
