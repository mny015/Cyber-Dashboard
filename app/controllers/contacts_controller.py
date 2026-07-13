"""HTTP handlers for user-owned contacts."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import validate_action
from app.forms.contacts import ContactForm
from app.models.contact import Contact
from app.repositories import contact_repository
from utils.audit import log_audit


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
    form = ContactForm()
    if not form.validate_on_submit():
        return render_template("contacts/form.html", contact=None, form=form)

    contact = Contact(owner_id=current_user.id)
    _apply_form(contact, form)
    contact_repository.create(contact)
    log_audit("contact_created", f"Created contact {contact.id}")
    flash("Contact created successfully.", "success")
    return redirect(url_for("contacts.index"))


@login_required
def edit(contact_id):
    contact = _get_contact_or_404(contact_id)
    form = ContactForm(obj=contact)
    if not form.validate_on_submit():
        return render_template("contacts/form.html", contact=contact, form=form)

    _apply_form(contact, form)
    contact_repository.update_owned(contact, current_user.id)
    log_audit("contact_updated", f"Updated contact {contact.id}")
    flash("Contact updated successfully.", "success")
    return redirect(url_for("contacts.index"))


@login_required
def delete(contact_id):
    if not validate_action():
        return redirect(url_for("contacts.index"))
    contact = _get_contact_or_404(contact_id)
    contact_repository.delete_owned(contact.id, current_user.id)
    log_audit("contact_deleted", f"Deleted contact {contact.id}")
    flash("Contact deleted successfully.", "info")
    return redirect(url_for("contacts.index"))


def _apply_form(contact, form):
    contact.name = form.name.data
    contact.email = form.email.data.lower()
    contact.phone = form.phone.data
    contact.notes = form.notes.data or ""
