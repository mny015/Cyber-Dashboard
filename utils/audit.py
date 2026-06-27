from flask import current_app, request
from flask_login import current_user

from app.models import db
from app.models.audit_log import AuditLog


def log_audit(action, details="", user=None):
    actor = user
    if actor is None and current_user.is_authenticated:
        actor = current_user

    log = AuditLog(
        action=action,
        details=details,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr or ""),
        user_id=actor.id if actor else None,
    )
    db.session.add(log)
    current_app.logger.info("%s user_id=%s ip=%s %s", action, log.user_id, log.ip_address, details)
