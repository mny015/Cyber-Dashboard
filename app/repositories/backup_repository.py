"""Privacy-scoped export data assembly."""

from app.utils.database import db


def personal_data(user_id):
    user_id = int(user_id)
    account = (
        db.table("users")
        .select(
            "id", "email", "display_name", "role", "is_banned", "mfa_enabled",
            "profile_bio", "created_at", "updated_at",
        )
        .where("id", "=", user_id)
        .first()
    )
    return {
        "account": [account] if account else [],
        "categories": _owned_rows(
            "categories",
            ("id", "name", "description", "color", "is_deleted", "created_at", "updated_at"),
            user_id,
        ),
        "topics": _owned_rows(
            "topics",
            (
                "id", "title", "slug", "description", "status", "priority", "notes",
                "is_deleted", "category_id", "created_at", "updated_at",
            ),
            user_id,
        ),
        "notes": _owned_rows(
            "notes",
            ("id", "title", "body", "topic_id", "is_deleted", "created_at", "updated_at"),
            user_id,
        ),
        "contacts": _owned_rows(
            "contacts",
            ("id", "name", "email", "phone", "notes", "is_deleted", "created_at", "updated_at"),
            user_id,
        ),
        "labs": db.named_query("export_personal_labs", {"user_id": user_id}),
        "lab_completions": db.named_query(
            "export_personal_lab_completions", {"user_id": user_id}
        ),
        "note_access_requests": db.named_query(
            "export_personal_note_requests", {"user_id": user_id}
        ),
    }


def admin_data(admin_id):
    admin_id = int(admin_id)
    data = personal_data(admin_id)
    data.update(
        {
            "system_users": (
                db.table("users")
                .select(
                    "id", "email", "display_name", "role", "is_banned",
                    "mfa_enabled", "created_at", "updated_at",
                )
                .order_by("id", "ASC")
                .all()
            ),
            "system_categories": db.named_query("export_system_categories"),
            "system_topics": db.named_query("export_system_topics"),
            "shared_labs": db.named_query("export_shared_labs"),
            "approved_notes": db.named_query(
                "export_approved_notes", {"admin_id": admin_id}
            ),
            "audit_logs": db.named_query("export_audit_logs"),
        }
    )
    return data


def _owned_rows(table_name, columns, owner_id):
    return (
        db.table(table_name)
        .select(*columns)
        .where("owner_id", "=", int(owner_id))
        .order_by("id", "ASC")
        .all()
    )
