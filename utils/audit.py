from flask import current_app, request
from flask_login import current_user

from app.services import audit_service


def get_audit_context(user=None):
    """Build the HTTP-specific context passed into pure business services."""
    actor = user
    if actor is None and current_user.is_authenticated:
        actor = current_user
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    ip_address = forwarded_for.split(",", 1)[0].strip() or request.remote_addr or ""
    return audit_service.AuditContext(
        actor_id=actor.id if actor else None,
        ip_address=ip_address,
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
