from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.contact import Contact
from utils.db import execute, fetch_all, fetch_one
from utils.helpers import clean_text, is_valid_email, is_valid_phone

contacts_bp = Blueprint("contacts", __name__, url_prefix="/contacts")


def get_contact_or_404(contact_id):
    contact = Contact.from_row(
        fetch_one(
            "SELECT * FROM contacts WHERE id = %s AND owner_id = %s AND is_deleted = 0",
            (contact_id, current_user.id),
        )
    )
    if not contact:
        abort(404)
    return contact


@contacts_bp.route("/")
@login_required
def index():
    contacts = [
        Contact.from_row(row)
        for row in fetch_all(
            "SELECT * FROM contacts WHERE owner_id = %s AND is_deleted = 0 ORDER BY name ASC",
            (current_user.id,),
        )
    ]
    return render_template("contacts/index.html", contacts=contacts)


@contacts_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    contact = Contact(owner_id=current_user.id)
    if request.method == "POST":
        apply_contact_form(contact)
        if not validate_contact(contact):
            return render_template("contacts/form.html", contact=contact)

        _, contact.id = execute(
            """
            INSERT INTO contacts (name, email, phone, notes, is_deleted, owner_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 0, %s, NOW(), NOW())
            """,
            (contact.name, contact.email, contact.phone, contact.notes, contact.owner_id),
        )
        flash("Contact created successfully.", "success")
        return redirect(url_for("contacts.index"))

    return render_template("contacts/form.html", contact=None)


@contacts_bp.route("/<int:contact_id>/edit", methods=["GET", "POST"])
@login_required
def edit(contact_id):
    contact = get_contact_or_404(contact_id)
    if request.method == "POST":
        apply_contact_form(contact)
        if not validate_contact(contact):
            return render_template("contacts/form.html", contact=contact)

        execute(
            """
            UPDATE contacts
            SET name = %s, email = %s, phone = %s, notes = %s, updated_at = NOW()
            WHERE id = %s AND owner_id = %s AND is_deleted = 0
            """,
            (contact.name, contact.email, contact.phone, contact.notes, contact.id, current_user.id),
        )
        flash("Contact updated successfully.", "success")
        return redirect(url_for("contacts.index"))

    return render_template("contacts/form.html", contact=contact)


@contacts_bp.route("/<int:contact_id>/delete", methods=["POST"])
@login_required
def delete(contact_id):
    contact = get_contact_or_404(contact_id)
    execute(
        "UPDATE contacts SET is_deleted = 1, updated_at = NOW() WHERE id = %s AND owner_id = %s",
        (contact.id, current_user.id),
    )
    flash("Contact deleted successfully.", "info")
    return redirect(url_for("contacts.index"))


def apply_contact_form(contact):
    contact.name = clean_text(request.form.get("name"))
    contact.email = clean_text(request.form.get("email"))
    contact.phone = clean_text(request.form.get("phone"))
    contact.notes = clean_text(request.form.get("notes"))


def validate_contact(contact):
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
