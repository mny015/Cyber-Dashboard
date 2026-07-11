from dataclasses import dataclass
from datetime import date, datetime
from typing import ClassVar

from app.models.base import RowModel


@dataclass(slots=True)
class WorkLog(RowModel):
    TABLE_NAME: ClassVar[str] = "work_logs"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "title", "log_type", "content", "evidence_url", "risk_rating",
        "log_date", "owner_id", "created_at", "updated_at",
    )

    id: int | None = None
    title: str = ""
    log_type: str = ""
    content: str = ""
    evidence_url: str = ""
    risk_rating: str = ""
    log_date: date | None = None
    owner_id: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class RoadmapItem(RowModel):
    TABLE_NAME: ClassVar[str] = "roadmap_items"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "title", "milestone", "status", "due_date", "topic_id",
        "owner_id", "created_at", "updated_at",
    )

    id: int | None = None
    title: str = ""
    milestone: str = ""
    status: str = ""
    due_date: date | None = None
    topic_id: int | None = None
    owner_id: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ProgressReflection(RowModel):
    TABLE_NAME: ClassVar[str] = "progress_reflections"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "insight", "challenge", "next_step", "owner_id", "created_at",
        "updated_at",
    )

    id: int | None = None
    insight: str = ""
    challenge: str = ""
    next_step: str = ""
    owner_id: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ActivityEvent(RowModel):
    TABLE_NAME: ClassVar[str] = "activity_events"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "event_type", "intensity", "occurred_on", "owner_id",
        "created_at", "updated_at",
    )

    id: int | None = None
    event_type: str = ""
    intensity: int = 0
    occurred_on: date | None = None
    owner_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
