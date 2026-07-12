"""Ownership-scoped contact persistence."""

from datetime import datetime

from app.models import Contact
from app.utils.database import db


def find_owned(contact_id, owner_id):
    row = (
        db.table(Contact.TABLE_NAME)
        .where("id", "=", int(contact_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .first()
    )
    return Contact.from_row(row)


def list_for_user(owner_id):
    rows = (
        db.table(Contact.TABLE_NAME)
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .order_by("name", "ASC")
        .all()
    )
    return Contact.from_rows(rows)


def create(contact):
    now = datetime.now()
    result = db.table(Contact.TABLE_NAME).insert(
        {
            "name": contact.name,
            "email": contact.email,
            "phone": contact.phone,
            "notes": contact.notes,
            "is_deleted": False,
            "owner_id": contact.owner_id,
            "created_at": now,
            "updated_at": now,
        }
    )
    contact.id = result.last_insert_id
    return contact


def update_owned(contact, owner_id):
    return (
        db.table(Contact.TABLE_NAME)
        .where("id", "=", int(contact.id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update(
            {
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "notes": contact.notes,
                "updated_at": datetime.now(),
            }
        )
    )


def delete_owned(contact_id, owner_id):
    return (
        db.table(Contact.TABLE_NAME)
        .where("id", "=", int(contact_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update({"is_deleted": True, "updated_at": datetime.now()})
    )
