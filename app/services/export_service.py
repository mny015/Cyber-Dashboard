"""Privacy-scoped export assembly with centralized audit evidence."""

from app.repositories import backup_repository
from app.services import audit_service


def personal_export(user_id, export_format, context):
    data = personal_data(user_id)
    record_personal_export(export_format, context)
    return data


def admin_export(admin_id, export_format, context):
    data = admin_data(admin_id)
    record_admin_export(export_format, context)
    return data


def personal_data(user_id):
    return backup_repository.personal_data(user_id)


def admin_data(admin_id):
    return backup_repository.admin_data(admin_id)


def record_personal_export(export_format, context):
    audit_service.record(
        "personal_backup_exported",
        f"Exported personal data as {_format_label(export_format)}",
        context,
    )


def record_admin_export(export_format, context):
    audit_service.record(
        "admin_backup_exported",
        f"Exported privacy-aware system data as {_format_label(export_format)}",
        context,
    )


def _format_label(export_format):
    return "CSV archive" if export_format == "zip" else "JSON"
