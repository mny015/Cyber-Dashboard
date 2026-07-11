from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from app.models.base import RowModel


@dataclass(slots=True)
class ProfileImage(RowModel):
    TABLE_NAME: ClassVar[str] = "profile_images"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "image_hash", "image_data", "mime_type", "byte_size", "created_at",
    )

    image_hash: str = ""
    image_data: bytes = b""
    mime_type: str = ""
    byte_size: int = 0
    created_at: datetime | None = None
