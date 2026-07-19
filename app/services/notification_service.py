"""Note-access request, approval, denial, and notification workflows."""

from app.repositories import notification_repository
from app.services import audit_service
from app.services.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.utils.database import db, transaction


def request_note_access(topic_id, admin_id, context):
    with transaction() as cursor:
        database = db.using(cursor)
        topic = notification_repository.find_topic_for_admin(topic_id, database=database)
        if not topic:
            raise NotFoundError("Topic not found.")
        if topic.owner_id == admin_id:
            raise PermissionDeniedError("You already own this topic.")
        existing = notification_repository.find_existing_for_admin(
            topic_id, admin_id, database=database
        )
        if existing:
            raise ConflictError(f"A {existing.status} request already exists for this topic.")
        request_id = notification_repository.create_request(
            topic_id, admin_id, database=database
        )
        audit_service.record(
            "note_access_requested",
            f"Requested notes for topic {topic.title}",
            context,
            database,
        )
    return request_id


def approve_request(request_id, owner_id, note_id, context):
    with transaction() as cursor:
        if not notification_repository.approve_owned(
            request_id, owner_id, note_id, cursor=cursor
        ):
            raise PermissionDeniedError("Choose one of your notes for this topic.")
        audit_service.record(
            "note_access_approved",
            f"Approved note access request {request_id}",
            context,
            db.using(cursor),
        )


def deny_request(request_id, owner_id, context):
    with transaction() as cursor:
        if not notification_repository.deny_owned(request_id, owner_id, cursor=cursor):
            raise NotFoundError("Pending note access request not found.")
        audit_service.record(
            "note_access_denied",
            f"Denied note access request {request_id}",
            context,
            db.using(cursor),
        )
