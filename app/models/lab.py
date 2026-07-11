from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel, as_bool


@dataclass(slots=True)
class LabPlatform(RowModel):
    TABLE_NAME: ClassVar[str] = "lab_platforms"
    COLUMNS: ClassVar[tuple[str, ...]] = ("id", "name", "slug")

    id: int | None = None
    name: str = ""
    slug: str = ""


@dataclass(slots=True)
class LabReference(RowModel):
    TABLE_NAME: ClassVar[str] = "lab_references"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "name", "platform_id", "url", "notes", "topic_id", "owner_id",
        "visibility", "is_deleted", "created_at", "updated_at",
    )

    id: int | None = None
    name: str = ""
    platform_id: int = 0
    url: str = ""
    notes: str = ""
    topic_id: int | None = None
    owner_id: int = 0
    visibility: str = "personal"
    is_deleted: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    platform_name: str | None = None
    topic_title: str | None = None
    owner_name: str | None = None
    owner_role: str | None = None
    is_completed: bool = False
    completion_count: int | None = None

    def __post_init__(self):
        self.is_deleted = as_bool(self.is_deleted)
        self.is_completed = as_bool(self.is_completed)
        if self.completion_count is not None:
            self.completion_count = int(self.completion_count)


@dataclass(slots=True)
class LabCompletion(RowModel):
    TABLE_NAME: ClassVar[str] = "lab_completions"
    COLUMNS: ClassVar[tuple[str, ...]] = ("id", "lab_id", "user_id", "completed_at")

    id: int | None = None
    lab_id: int = 0
    user_id: int = 0
    completed_at: datetime | None = None
