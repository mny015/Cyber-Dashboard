from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel


@dataclass(slots=True)
class ScheduledTask(RowModel):
    TABLE_NAME: ClassVar[str] = "scheduled_tasks"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "user_id", "created_by", "title", "description", "task_type",
        "due_at", "status", "scope", "created_at", "updated_at",
    )

    id: int | None = None
    user_id: int | None = None
    created_by: int | None = None
    title: str = ""
    description: str | None = None
    task_type: str = "general"
    due_at: datetime | None = None
    status: str = "upcoming"
    scope: str = "personal"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    creator_name: str | None = None
    assignee_name: str | None = None
