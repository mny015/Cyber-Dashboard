from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel, as_bool


@dataclass(slots=True)
class Topic(RowModel):
    TABLE_NAME: ClassVar[str] = "topics"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "title", "slug", "description", "status", "priority", "notes",
        "is_deleted", "category_id", "owner_id", "created_at", "updated_at",
    )

    id: int | None = None
    title: str = ""
    slug: str = ""
    description: str = ""
    status: str = "planned"
    priority: str = "medium"
    notes: str = ""
    is_deleted: bool = False
    category_id: int | None = None
    owner_id: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    category_name: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None

    def __post_init__(self):
        self.is_deleted = as_bool(self.is_deleted)
