"""Data-only compatibility helpers used before legacy schema cleanup."""

import hashlib
from pathlib import Path, PurePosixPath


IMAGE_MIME_BY_TYPE = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


class LegacyDataError(RuntimeError):
    """Raised when a legacy value cannot be preserved safely."""


def prepare_legacy_profile_images(connection, project_root, output=print):
    """Move legacy profile image bytes into profile_images without changing schema."""
    if not _table_exists(connection, "users") or not _table_exists(connection, "profile_images"):
        return 0

    columns = _column_names(connection, "users")
    if "profile_image" not in columns:
        return 0

    imported = 0
    if "profile_image_data" in columns:
        imported += _import_embedded_images(connection, columns)
    imported += _import_static_images(connection, Path(project_root))
    _reject_unresolved_images(connection)

    if imported:
        output(f"[DATA] Preserved {imported} legacy profile image(s) in the database.")
    return imported


def _import_embedded_images(connection, columns):
    mime_expression = "profile_image_mime" if "profile_image_mime" in columns else "NULL"
    size_expression = "profile_image_size" if "profile_image_size" in columns else "NULL"
    query = f"""
        SELECT id, profile_image, profile_image_data,
               {mime_expression} AS profile_image_mime,
               {size_expression} AS profile_image_size
        FROM users
        WHERE profile_image_data IS NOT NULL
    """
    imported = 0
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            image_bytes = bytes(row["profile_image_data"])
            image_type = detect_image_type(image_bytes)
            if image_type not in IMAGE_MIME_BY_TYPE:
                continue
            _store_profile_image(cursor, row["id"], image_bytes, image_type)
            imported += 1
    return imported


def _import_static_images(connection, project_root):
    static_root = (project_root / "app" / "static").resolve()
    profile_root = (static_root / "uploads" / "profiles").resolve()
    imported = 0

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, profile_image
            FROM users
            WHERE profile_image IS NOT NULL AND profile_image <> ''
            """
        )
        rows = cursor.fetchall()
        for row in rows:
            old_path = str(row["profile_image"]).replace("\\", "/")
            if len(old_path) == 64 or not old_path.startswith("uploads/profiles/"):
                continue

            relative_path = Path(*PurePosixPath(old_path).parts)
            disk_path = (static_root / relative_path).resolve()
            try:
                disk_path.relative_to(profile_root)
            except ValueError as exc:
                raise LegacyDataError(f"Unsafe legacy profile image path for user {row['id']}.") from exc
            if not disk_path.is_file():
                continue

            image_bytes = disk_path.read_bytes()
            image_type = detect_image_type(image_bytes)
            if image_type not in IMAGE_MIME_BY_TYPE:
                continue
            _store_profile_image(cursor, row["id"], image_bytes, image_type)
            imported += 1
    return imported


def _store_profile_image(cursor, user_id, image_bytes, image_type):
    digest = hashlib.sha256(image_bytes).hexdigest()
    cursor.execute(
        """
        INSERT INTO profile_images (image_hash, image_data, mime_type, byte_size, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE image_hash = VALUES(image_hash)
        """,
        (digest, image_bytes, IMAGE_MIME_BY_TYPE[image_type], len(image_bytes)),
    )
    cursor.execute("UPDATE users SET profile_image = %s WHERE id = %s", (digest, user_id))


def _reject_unresolved_images(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT users.id, users.profile_image
            FROM users
            LEFT JOIN profile_images
              ON profile_images.image_hash = users.profile_image
            WHERE users.profile_image IS NOT NULL
              AND users.profile_image <> ''
              AND (
                  CHAR_LENGTH(users.profile_image) <> 64
                  OR profile_images.image_hash IS NULL
              )
            ORDER BY users.id
            """
        )
        unresolved = cursor.fetchall()

    if unresolved:
        user_ids = ", ".join(str(row["id"]) for row in unresolved[:10])
        raise LegacyDataError(
            "Legacy profile image data could not be preserved for user ID(s): "
            f"{user_ids}. Restore the referenced files or clear those image references "
            "after taking a backup, then rerun migrations."
        )


def _table_exists(connection, table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = %s
            """,
            (table_name,),
        )
        return cursor.fetchone()["total"] > 0


def _column_names(connection, table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name AS column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = %s
            """,
            (table_name,),
        )
        return {row["column_name"] for row in cursor.fetchall()}


def detect_image_type(file_bytes):
    header = file_bytes[:512]
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"
    return None
