"""Note-access request persistence for user notifications and admin review."""

from datetime import datetime

from app.models import Note, NoteAccessRequest, Notification, Topic
from app.utils.database import db, transaction


def list_for_owner(owner_id):
    rows = db.named_query("notifications_for_owner", {"owner_id": int(owner_id)})
    return Notification.from_rows(rows)


def list_notes_for_topic(owner_id, topic_id):
    rows = (
        db.table(Note.TABLE_NAME)
        .select("id", "title")
        .where("owner_id", "=", int(owner_id))
        .where("topic_id", "=", int(topic_id))
        .where("is_deleted", "=", False)
        .order_by("updated_at", "DESC")
        .all()
    )
    return Note.from_rows(rows)


def find_pending_owned(request_id, owner_id):
    row = db.named_query(
        "pending_note_request_owned",
        {"request_id": int(request_id), "owner_id": int(owner_id)},
        fetch="one",
    )
    return NoteAccessRequest.from_row(row)


def approve_owned(request_id, owner_id, note_id, cursor=None):
    if cursor is not None:
        return _approve(cursor, request_id, owner_id, note_id)
    with transaction() as transaction_cursor:
        return _approve(transaction_cursor, request_id, owner_id, note_id)


def _approve(cursor, request_id, owner_id, note_id):
    cursor.execute(
            """
            UPDATE note_access_requests AS requests
            JOIN topics ON topics.id = requests.topic_id
            JOIN notes
              ON notes.id = %s
             AND notes.topic_id = requests.topic_id
             AND notes.owner_id = topics.owner_id
             AND notes.is_deleted = 0
            SET requests.status = 'approved',
                requests.note_id = notes.id,
                requests.responded_at = NOW()
            WHERE requests.id = %s
              AND requests.status = 'pending'
              AND topics.owner_id = %s
            """,
            (int(note_id), int(request_id), int(owner_id)),
    )
    return cursor.rowcount


def deny_owned(request_id, owner_id, cursor=None):
    if cursor is not None:
        return _deny(cursor, request_id, owner_id)
    with transaction() as transaction_cursor:
        return _deny(transaction_cursor, request_id, owner_id)


def _deny(cursor, request_id, owner_id):
    cursor.execute(
            """
            UPDATE note_access_requests AS requests
            JOIN topics ON topics.id = requests.topic_id
            SET requests.status = 'denied', requests.responded_at = NOW()
            WHERE requests.id = %s
              AND requests.status = 'pending'
              AND topics.owner_id = %s
            """,
            (int(request_id), int(owner_id)),
    )
    return cursor.rowcount


def find_topic_for_admin(topic_id, database=None):
    database = database or db
    row = (
        database.table(Topic.TABLE_NAME)
        .select("id", "owner_id", "title")
        .where("id", "=", int(topic_id))
        .where("is_deleted", "=", False)
        .first()
    )
    return Topic.from_row(row)


def find_existing_for_admin(topic_id, admin_id, database=None):
    database = database or db
    row = (
        database.table(NoteAccessRequest.TABLE_NAME)
        .where("topic_id", "=", int(topic_id))
        .where("requester_admin_id", "=", int(admin_id))
        .where_in("status", ("pending", "approved"))
        .order_by("requested_at", "DESC")
        .first()
    )
    return NoteAccessRequest.from_row(row)


def create_request(topic_id, admin_id, database=None):
    database = database or db
    result = database.table(NoteAccessRequest.TABLE_NAME).insert(
        {
            "topic_id": int(topic_id),
            "note_id": None,
            "requester_admin_id": int(admin_id),
            "status": "pending",
            "requested_at": datetime.now(),
            "responded_at": None,
        }
    )
    return result.last_insert_id


def list_for_admin(admin_id):
    rows = db.named_query("note_requests_for_admin", {"admin_id": int(admin_id)})
    return NoteAccessRequest.from_rows(rows)


def find_approved_note(request_id, admin_id):
    return db.named_query(
        "approved_note_for_admin",
        {"request_id": int(request_id), "admin_id": int(admin_id)},
        fetch="one",
    )
