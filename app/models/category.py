from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel, as_bool


@dataclass(slots=True)
class Category(RowModel):
    TABLE_NAME: ClassVar[str] = "categories"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "name", "description", "color", "is_deleted", "owner_id",
        "created_at", "updated_at",
    )

    id: int | None = None
    name: str = ""
    description: str = ""
    color: str = "#2563eb"
    is_deleted: bool = False
    owner_id: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    topic_count: int | None = None

    def __post_init__(self):
        self.is_deleted = as_bool(self.is_deleted)
        if self.topic_count is not None:
            self.topic_count = int(self.topic_count)
