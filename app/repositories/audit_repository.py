"""Persistence and reporting operations for audit events."""

from dataclasses import dataclass
from datetime import datetime
from math import ceil

from app.models import AuditLog
from app.utils.database import db


@dataclass(frozen=True, slots=True)
class AuditPage:
    items: list[AuditLog]
    page: int
    per_page: int
    total: int
    pages: int

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None

    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None


def create(action, details, ip_address, user_id=None, database=None):
    database = database or db
    result = database.table(AuditLog.TABLE_NAME).insert(
        {
            "action": action,
            "details": details,
            "ip_address": ip_address,
            "user_id": user_id,
            "created_at": datetime.now(),
        }
    )
    return result.last_insert_id


def paginate(page=1, per_page=25):
    page = max(int(page), 1)
    per_page = max(int(per_page), 1)
    total = db.table(AuditLog.TABLE_NAME).count()
    rows = db.named_query(
        "audit_logs_page",
        {"limit": per_page, "offset": (page - 1) * per_page},
    )
    return AuditPage(
        items=AuditLog.from_rows(rows),
        page=page,
        per_page=per_page,
        total=total,
        pages=ceil(total / per_page) if total else 0,
    )
