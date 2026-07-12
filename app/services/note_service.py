"""Transactional note write workflows with ownership and audit rules."""

from app.models import Note
from app.repositories import note_repository, topic_repository
from app.services import audit_service
from app.services.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.utils.database import db, transaction


def create_note(owner_id, title, body, topic_id, context):
    _validate_content(title, body)
    with transaction() as cursor:
        database = db.using(cursor)
        _require_owned_topic(topic_id, owner_id, database)
        note = note_repository.create(
            Note(title=title, body=body, topic_id=topic_id, owner_id=owner_id),
            database=database,
        )
        audit_service.record(
            "note_created", f"Created note {note.id}", context, database
        )
    return note


def update_note(note_id, owner_id, title, body, topic_id, context):
    _validate_content(title, body)
    with transaction() as cursor:
        database = db.using(cursor)
        note = note_repository.find_owned(note_id, owner_id, database=database)
        if not note:
            raise NotFoundError("Note not found.")
        _require_owned_topic(topic_id, owner_id, database)
        note.title = title
        note.body = body
        note.topic_id = topic_id
        result = note_repository.update_owned(note, owner_id, database=database)
        if not result.affected_rows:
            raise NotFoundError("Note not found.")
        audit_service.record(
            "note_updated", f"Updated note {note_id}", context, database
        )
    return note


def delete_note(note_id, owner_id, context):
    with transaction() as cursor:
        database = db.using(cursor)
        note = note_repository.find_owned(note_id, owner_id, database=database)
        if not note:
            raise NotFoundError("Note not found.")
        result = note_repository.delete_owned(note_id, owner_id, database=database)
        if not result.affected_rows:
            raise NotFoundError("Note not found.")
        audit_service.record(
            "note_deleted", f"Deleted note {note_id}", context, database
        )
    return note


def _validate_content(title, body):
    if not title or not body:
        raise ValidationError("Note title and body are required.")


def _require_owned_topic(topic_id, owner_id, database):
    if topic_id and not topic_repository.exists_owned(topic_id, owner_id, database=database):
        raise PermissionDeniedError("The selected topic is not owned by this user.")
