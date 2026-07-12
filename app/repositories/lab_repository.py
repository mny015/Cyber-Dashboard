"""Lab persistence with owner and shared-visibility enforcement."""

from datetime import datetime

from app.models import LabPlatform, LabReference
from app.utils.database import db, transaction


def list_visible(user_id, platform_id=None):
    rows = db.named_query(
        "visible_labs",
        {"user_id": int(user_id), "platform_id": platform_id},
    )
    return LabReference.from_rows(rows)


def find_visible(lab_id, user_id):
    row = db.named_query(
        "visible_lab",
        {"lab_id": int(lab_id), "user_id": int(user_id)},
        fetch="one",
    )
    return LabReference.from_row(row)


def find_owned(lab_id, owner_id):
    row = (
        db.table(LabReference.TABLE_NAME)
        .where("id", "=", int(lab_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .first()
    )
    return LabReference.from_row(row)


def list_platforms():
    rows = db.table(LabPlatform.TABLE_NAME).order_by("name", "ASC").all()
    return LabPlatform.from_rows(rows)


def platform_exists(platform_id):
    return db.table(LabPlatform.TABLE_NAME).where("id", "=", int(platform_id)).exists()


def create(lab):
    now = datetime.now()
    result = db.table(LabReference.TABLE_NAME).insert(
        {
            "name": lab.name,
            "platform_id": lab.platform_id,
            "url": lab.url,
            "notes": lab.notes,
            "topic_id": lab.topic_id,
            "owner_id": lab.owner_id,
            "visibility": lab.visibility,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
        }
    )
    lab.id = result.last_insert_id
    return lab


def update_owned(lab, owner_id):
    return (
        db.table(LabReference.TABLE_NAME)
        .where("id", "=", int(lab.id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update(
            {
                "name": lab.name,
                "platform_id": lab.platform_id,
                "url": lab.url,
                "notes": lab.notes,
                "topic_id": lab.topic_id,
                "visibility": lab.visibility,
                "updated_at": datetime.now(),
            }
        )
    )


def delete_owned(lab_id, owner_id):
    return (
        db.table(LabReference.TABLE_NAME)
        .where("id", "=", int(lab_id))
        .where("owner_id", "=", int(owner_id))
        .where("is_deleted", "=", False)
        .update({"is_deleted": True, "updated_at": datetime.now()})
    )


def mark_completed_if_visible(lab_id, user_id):
    with transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO lab_completions (lab_id, user_id, completed_at)
            SELECT labs.id, %s, NOW()
            FROM lab_references AS labs
            JOIN users AS owners ON owners.id = labs.owner_id
            WHERE labs.id = %s
              AND labs.is_deleted = 0
              AND (
                    labs.owner_id = %s
                 OR (labs.visibility = 'public' AND owners.role = 'admin')
              )
            ON DUPLICATE KEY UPDATE completed_at = VALUES(completed_at)
            """,
            (int(user_id), int(lab_id), int(user_id)),
        )
        return cursor.rowcount


def mark_incomplete(lab_id, user_id):
    return (
        db.table("lab_completions")
        .where("lab_id", "=", int(lab_id))
        .where("user_id", "=", int(user_id))
        .delete()
    )
