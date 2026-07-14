"""Compatibility imports; application code uses app.utils.audit."""

from app.utils.audit import get_audit_context, log_audit


__all__ = ["get_audit_context", "log_audit"]
