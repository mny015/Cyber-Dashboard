"""Explicit persistence operations for user accounts and profile data."""

from datetime import datetime

from app.models import ProfileImage, User
from app.utils.database import db, transaction


def find_by_id(user_id, database=None):
    try:
        normalized_id = int(user_id)
    except (TypeError, ValueError):
        return None
    database = database or db
    return User.from_row(database.table(User.TABLE_NAME).where("id", "=", normalized_id).first())


def find_by_email(email, database=None):
    database = database or db
    return User.from_row(
        database.table(User.TABLE_NAME).where("email", "=", email).first()
    )


def list_all():
    rows = db.table(User.TABLE_NAME).order_by("created_at", "DESC").all()
    return User.from_rows(rows)


def email_in_use(email, exclude_user_id=None):
    query = db.table(User.TABLE_NAME).where("email", "=", email)
    if exclude_user_id is not None:
        query.where("id", "!=", int(exclude_user_id))
    return query.exists()


def create(user, database=None):
    database = database or db
    now = datetime.now()
    result = database.table(User.TABLE_NAME).insert(
        {
            "email": user.email,
            "password_hash": user.password_hash,
            "display_name": user.display_name,
            "role": user.role,
            "is_banned": user.is_banned,
            "mfa_secret": user.mfa_secret,
            "mfa_enabled": user.mfa_enabled,
            "created_at": now,
            "updated_at": now,
        }
    )
    user.id = result.last_insert_id
    user.created_at = now
    user.updated_at = now
    return user


def update_role(user_id, role, database=None):
    return _update_user(user_id, {"role": role}, database=database)


def set_banned(user_id, is_banned, database=None):
    return _update_user(user_id, {"is_banned": bool(is_banned)}, database=database)


def set_mfa_secret(user_id, secret, database=None):
    return _update_user(user_id, {"mfa_secret": secret}, database=database)


def set_mfa_enabled(user_id, enabled, database=None):
    return _update_user(user_id, {"mfa_enabled": bool(enabled)}, database=database)


def update_password(user_id, password_hash, auth_version, reset_failures=False, database=None):
    database = database or db
    values = {
        "password_hash": password_hash,
        "auth_version": int(auth_version),
        "updated_at": datetime.now(),
    }
    if reset_failures:
        values.update(
            {
                "failed_login_count": 0,
                "last_failed_login_at": None,
                "locked_until": None,
            }
        )
    return database.table(User.TABLE_NAME).where("id", "=", int(user_id)).update(values)


def record_failed_login(user_id, failure_limit, lockout_minutes, cursor=None):
    """Atomically increment failures and establish the lockout timestamp."""
    if cursor is not None:
        return _record_failed_login(cursor, user_id, failure_limit, lockout_minutes)
    with transaction() as transaction_cursor:
        return _record_failed_login(
            transaction_cursor, user_id, failure_limit, lockout_minutes
        )


def _record_failed_login(cursor, user_id, failure_limit, lockout_minutes):
    cursor.execute(
            """
            UPDATE users
            SET failed_login_count = failed_login_count + 1,
                last_failed_login_at = NOW(),
                locked_until = CASE
                    WHEN failed_login_count + 1 >= %s
                    THEN TIMESTAMPADD(MINUTE, %s, NOW())
                    ELSE locked_until
                END,
                updated_at = NOW()
            WHERE id = %s
            """,
            (int(failure_limit), int(lockout_minutes), int(user_id)),
    )
    return cursor.rowcount


def reset_failed_logins(user_id, database=None):
    return _update_user(
        user_id,
        {
            "failed_login_count": 0,
            "last_failed_login_at": None,
            "locked_until": None,
        },
        database=database,
    )


def count_other_active_admins(user_id, database=None):
    database = database or db
    return (
        database.table(User.TABLE_NAME)
        .where("role", "=", "admin")
        .where("is_banned", "=", False)
        .where("id", "!=", int(user_id))
        .count()
    )


def find_owned_profile_image(user_id, image_hash):
    row = db.named_query(
        "owned_profile_image",
        {"user_id": int(user_id), "image_hash": image_hash},
        fetch="one",
    )
    return ProfileImage.from_row(row)


def update_profile(user_id, display_name, email, profile_bio, image=None):
    if image is None:
        return _update_user(
            user_id,
            {"display_name": display_name, "email": email, "profile_bio": profile_bio},
        )

    with transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO profile_images
                (image_hash, image_data, mime_type, byte_size, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE image_hash = VALUES(image_hash)
            """,
            (image.image_hash, image.image_data, image.mime_type, image.byte_size),
        )
        cursor.execute(
            """
            UPDATE users
            SET display_name = %s, email = %s, profile_bio = %s,
                profile_image = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (display_name, email, profile_bio, image.image_hash, int(user_id)),
        )
        return cursor.rowcount


def delete(user_id, cursor=None):
    """Delete one account and remove profile images no account references."""
    if cursor is not None:
        return _delete(cursor, user_id)
    with transaction() as transaction_cursor:
        return _delete(transaction_cursor, user_id)


def _delete(cursor, user_id):
    cursor.execute("DELETE FROM users WHERE id = %s", (int(user_id),))
    deleted = cursor.rowcount
    cursor.execute(
            """
            DELETE profile_images
            FROM profile_images
            LEFT JOIN users ON users.profile_image = profile_images.image_hash
            WHERE users.id IS NULL
            """
    )
    return deleted


def _update_user(user_id, values, database=None):
    database = database or db
    values = {**values, "updated_at": datetime.now()}
    return database.table(User.TABLE_NAME).where("id", "=", int(user_id)).update(values)
