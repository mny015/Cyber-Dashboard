from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel


@dataclass(slots=True)
class NoteAccessRequest(RowModel):
    TABLE_NAME: ClassVar[str] = "note_access_requests"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "topic_id", "requester_admin_id", "status",
        "requested_at", "responded_at",
    )

    id: int | None = None
    topic_id: int = 0
    note_id: int | None = None
    requester_admin_id: int | None = None
    status: str = "pending"
    requested_at: datetime | None = None
    responded_at: datetime | None = None
    topic_title: str | None = None
    admin_name: str | None = None
    admin_email: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    note_title: str | None = None


@dataclass(slots=True)
class NoteAccessGrant(RowModel):
    """The note selected when a topic-level access request is approved."""

    TABLE_NAME: ClassVar[str] = "note_access_grants"
    COLUMNS: ClassVar[tuple[str, ...]] = ("request_id", "note_id", "granted_at")

    request_id: int = 0
    note_id: int = 0
    granted_at: datetime | None = None


@dataclass(slots=True)
class Notification(NoteAccessRequest):
    """User-facing view of a note access request; it has no separate table."""
