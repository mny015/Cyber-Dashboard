"""Compatibility imports; application code uses app.utils.decorators."""

from app.utils.decorators import admin_required, role_required


__all__ = ["admin_required", "role_required"]
