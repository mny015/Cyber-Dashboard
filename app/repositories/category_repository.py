"""Ownership-scoped category persistence."""

from datetime import datetime

from app.models import Category
from app.utils.database import db


def find_owned(category_id, owner_id):
    row = (
        db.table(Category.TABLE_NAME)
        .where("id", "=", int(category_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .first()
    )
    return Category.from_row(row)


def list_for_user(owner_id):
    rows = (
        db.table(Category.TABLE_NAME)
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .order_by("name", "ASC")
        .all()
    )
    return Category.from_rows(rows)


def list_admin_summaries():
    return Category.from_rows(db.named_query("admin_category_summaries"))


def create(category):
    now = datetime.now()
    result = db.table(Category.TABLE_NAME).insert(
        {
            "name": category.name,
            "description": category.description,
            "color": category.color,
            "is_deleted": False,
            "owner_id": category.owner_id,
            "created_at": now,
            "updated_at": now,
        }
    )
    category.id = result.last_insert_id
    return category


def update_owned(category, owner_id):
    return (
        db.table(Category.TABLE_NAME)
        .where("id", "=", int(category.id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update(
            {
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "updated_at": datetime.now(),
            }
        )
    )


def delete_owned(category_id, owner_id):
    return (
        db.table(Category.TABLE_NAME)
        .where("id", "=", int(category_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update({"is_deleted": True, "updated_at": datetime.now()})
    )
