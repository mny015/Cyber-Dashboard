from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel, as_bool


@dataclass(slots=True)
class VulnerabilityCatalogEntry(RowModel):
    TABLE_NAME: ClassVar[str] = "vulnerability_catalog"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "code", "name", "category", "default_severity", "description",
        "source", "approval_status", "is_active", "created_by_user_id",
        "reviewed_by_user_id", "reviewed_at", "created_at", "updated_at",
    )

    id: int | None = None
    code: str = ""
    name: str = ""
    category: str = ""
    default_severity: str = "medium"
    description: str = ""
    source: str = ""
    approval_status: str = "pending"
    is_active: bool = False
    created_by_user_id: int | None = None
    reviewed_by_user_id: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    requested_by: str | None = None

    def __post_init__(self):
        self.is_active = as_bool(self.is_active)


@dataclass(slots=True)
class ThreatCatalogEntry(RowModel):
    TABLE_NAME: ClassVar[str] = "threat_catalog"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "code", "name", "default_level", "description", "source",
        "is_active", "created_at", "updated_at",
    )

    id: int | None = None
    code: str = ""
    name: str = ""
    default_level: str = "medium"
    description: str = ""
    source: str = ""
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        self.is_active = as_bool(self.is_active)


@dataclass(slots=True)
class SecurityFinding(RowModel):
    TABLE_NAME: ClassVar[str] = "security_findings"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "owner_id", "vulnerability_id", "threat_id", "activity_type",
        "title", "target", "severity", "status", "evidence", "notes",
        "detected_at", "is_deleted", "created_at", "updated_at",
    )

    id: int | None = None
    owner_id: int = 0
    vulnerability_id: int | None = None
    threat_id: int | None = None
    activity_type: str = ""
    title: str = ""
    target: str = ""
    severity: str = "medium"
    status: str = "open"
    evidence: str = ""
    notes: str = ""
    detected_at: datetime | None = None
    is_deleted: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    vulnerability_name: str | None = None
    vulnerability_code: str | None = None
    threat_name: str | None = None
    threat_code: str | None = None

    def __post_init__(self):
        self.is_deleted = as_bool(self.is_deleted)
