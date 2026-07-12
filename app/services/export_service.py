"""Privacy-scoped export assembly with centralized audit evidence."""

from app.repositories import backup_repository
from app.services import audit_service


def personal_export(user_id, export_format, context):
    data = backup_repository.personal_data(user_id)
    audit_service.record(
        "personal_backup_exported",
        f"Exported personal data as {_format_label(export_format)}",
        context,
    )
    return data


def admin_export(admin_id, export_format, context):
    data = backup_repository.admin_data(admin_id)
    audit_service.record(
        "admin_backup_exported",
        f"Exported privacy-aware system data as {_format_label(export_format)}",
        context,
    )
    return data


def _format_label(export_format):
    return "CSV archive" if export_format == "zip" else "JSON"
