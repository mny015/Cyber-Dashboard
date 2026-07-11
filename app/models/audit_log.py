from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel


@dataclass(slots=True)
class AuditLog(RowModel):
    TABLE_NAME: ClassVar[str] = "audit_logs"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "action", "details", "ip_address", "user_id", "created_at",
    )

    id: int | None = None
    action: str = ""
    details: str = ""
    ip_address: str = ""
    user_id: int | None = None
    created_at: datetime | None = None
    user_email: str | None = None
    user_name: str | None = None
