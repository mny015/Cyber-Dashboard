from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel, as_bool


@dataclass(slots=True)
class Note(RowModel):
    TABLE_NAME: ClassVar[str] = "notes"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "title", "body", "topic_id", "owner_id", "is_deleted",
        "created_at", "updated_at",
    )

    id: int | None = None
    title: str = ""
    body: str = ""
    topic_id: int | None = None
    owner_id: int = 0
    is_deleted: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    topic_title: str | None = None

    def __post_init__(self):
        self.is_deleted = as_bool(self.is_deleted)
