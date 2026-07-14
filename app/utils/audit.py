"""HTTP adapter for privacy-aware audit service context."""

from flask import current_app
from flask_login import current_user

from app.services import audit_service
from app.utils.security import get_client_address


def get_audit_context(user=None):
    actor = user
    if actor is None and current_user.is_authenticated:
        actor = current_user
    return audit_service.AuditContext(
        actor_id=actor.id if actor else None,
        ip_address=get_client_address(),
    )


def log_audit(action, details="", user=None):
    context = get_audit_context(user)
    audit_service.record(action, details, context)
    current_app.logger.info(
        "%s user_id=%s ip=%s %s",
        action,
        context.actor_id,
        context.ip_address,
        details,
    )
