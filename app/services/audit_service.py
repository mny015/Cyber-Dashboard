"""Central audit-event creation used by transactional business services."""

from dataclasses import dataclass

from app.repositories import audit_repository


@dataclass(frozen=True, slots=True)
class AuditContext:
    actor_id: int | None = None
    ip_address: str = ""


def record(action, details="", context=None, database=None):
    context = context or AuditContext()
    return audit_repository.create(
        action=action,
        details=details,
        ip_address=context.ip_address,
        user_id=context.actor_id,
        database=database,
    )
