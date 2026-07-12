"""Ownership-scoped topic persistence and joined topic lists."""

from datetime import datetime

from app.models import Topic
from app.utils.database import db


def find_owned(topic_id, owner_id):
    row = db.named_query(
        "owned_topic",
        {"topic_id": int(topic_id), "owner_id": int(owner_id)},
        fetch="one",
    )
    return Topic.from_row(row)


def exists_owned(topic_id, owner_id):
    return (
        db.table(Topic.TABLE_NAME)
        .where("id", "=", int(topic_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .exists()
    )


def list_for_user(owner_id, category_id=None):
    rows = db.named_query(
        "topics_for_user",
        {"owner_id": int(owner_id), "category_id": category_id},
    )
    return Topic.from_rows(rows)


def list_active(owner_id):
    rows = (
        db.table(Topic.TABLE_NAME)
        .select("id", "title")
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .order_by("title", "ASC")
        .all()
    )
    return Topic.from_rows(rows)


def list_admin_summaries():
    return Topic.from_rows(db.named_query("admin_topic_summaries"))


def slug_exists(owner_id, slug, exclude_topic_id=None):
    query = (
        db.table(Topic.TABLE_NAME)
        .where("owner_id", "=", int(owner_id))
        .where("slug", "=", slug)
        .where("is_deleted", "=", False)
    )
    if exclude_topic_id is not None:
        query.where("id", "!=", int(exclude_topic_id))
    return query.exists()


def create(topic):
    now = datetime.now()
    result = db.table(Topic.TABLE_NAME).insert(
        {
            "title": topic.title,
            "slug": topic.slug,
            "description": topic.description,
            "status": topic.status,
            "priority": topic.priority,
            "notes": topic.notes,
            "is_deleted": False,
            "category_id": topic.category_id,
            "owner_id": topic.owner_id,
            "created_at": now,
            "updated_at": now,
        }
    )
    topic.id = result.last_insert_id
    return topic


def update_owned(topic, owner_id):
    return (
        db.table(Topic.TABLE_NAME)
        .where("id", "=", int(topic.id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update(
            {
                "title": topic.title,
                "slug": topic.slug,
                "description": topic.description,
                "status": topic.status,
                "priority": topic.priority,
                "notes": topic.notes,
                "category_id": topic.category_id,
                "updated_at": datetime.now(),
            }
        )
    )


def delete_owned(topic_id, owner_id):
    return (
        db.table(Topic.TABLE_NAME)
        .where("id", "=", int(topic_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update({"is_deleted": True, "updated_at": datetime.now()})
    )
