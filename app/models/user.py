"""Plain user data model used by Flask-Login."""

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from flask_login import UserMixin
from app.models.base import RowModel, as_bool
from app.utils.security import hash_password, verify_password


@dataclass(slots=True)
class User(UserMixin, RowModel):
    TABLE_NAME: ClassVar[str] = "users"
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "id", "email", "password_hash", "display_name", "role", "is_banned",
        "mfa_secret", "mfa_enabled", "auth_version", "failed_login_count",
        "last_failed_login_at", "locked_until", "profile_bio", "profile_image",
        "created_at", "updated_at",
    )

    id: int | None = None
    email: str = ""
    password_hash: str = ""
    display_name: str = ""
    role: str = "user"
    is_banned: bool = False
    mfa_secret: str | None = None
    mfa_enabled: bool = False
    auth_version: int = 0
    failed_login_count: int = 0
    last_failed_login_at: datetime | None = None
    locked_until: datetime | None = None
    profile_bio: str | None = None
    profile_image: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        self.is_banned = as_bool(self.is_banned)
        self.mfa_enabled = as_bool(self.mfa_enabled)
        self.auth_version = int(self.auth_version or 0)
        self.failed_login_count = int(self.failed_login_count or 0)

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"
