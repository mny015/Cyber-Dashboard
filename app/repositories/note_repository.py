"""Ownership-scoped note persistence and note reporting queries."""

from datetime import datetime

from app.models import Note
from app.utils.database import db


def find_owned(note_id, owner_id, database=None):
    database = database or db
    row = database.named_query(
        "owned_note",
        {"note_id": int(note_id), "owner_id": int(owner_id)},
        fetch="one",
    )
    return Note.from_row(row)


def list_for_user(owner_id, topic_id=None, search=""):
    rows = db.named_query(
        "notes_for_user",
        {
            "owner_id": int(owner_id),
            "topic_id": topic_id,
            "search": search,
            "search_pattern": f"%{search}%",
        },
    )
    return Note.from_rows(rows)


def topic_summaries(owner_id):
    return db.named_query("note_topic_summaries", {"owner_id": int(owner_id)})


def stats_for_user(owner_id):
    return db.named_query(
        "note_stats",
        {"owner_id": int(owner_id)},
        fetch="one",
    ) or {"total_notes": 0, "last_updated": None}


def create(note, database=None):
    database = database or db
    now = datetime.now()
    result = database.table(Note.TABLE_NAME).insert(
        {
            "title": note.title,
            "body": note.body,
            "topic_id": note.topic_id,
            "owner_id": note.owner_id,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
        }
    )
    note.id = result.last_insert_id
    return note


def update_owned(note, owner_id, database=None):
    database = database or db
    return (
        database.table(Note.TABLE_NAME)
        .where("id", "=", int(note.id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update(
            {
                "title": note.title,
                "body": note.body,
                "topic_id": note.topic_id,
                "updated_at": datetime.now(),
            }
        )
    )


def delete_owned(note_id, owner_id, database=None):
    database = database or db
    return (
        database.table(Note.TABLE_NAME)
        .where("id", "=", int(note_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update({"is_deleted": True, "updated_at": datetime.now()})
    )
