from flask import current_app, request
from flask_login import current_user

from utils.db import execute


def log_audit(action, details="", user=None):
    actor = user
    if actor is None and current_user.is_authenticated:
        actor = current_user

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr or "")

    execute(
        """
        INSERT INTO audit_logs (action, details, ip_address, user_id, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (
            action,
            details,
            ip_address,
            actor.id if actor else None,
        ),
    )
    current_app.logger.info("%s user_id=%s ip=%s %s", action, actor.id if actor else None, ip_address, details)
