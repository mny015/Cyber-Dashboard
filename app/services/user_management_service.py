"""Administrative account changes with guard rules and atomic audit logs."""

from werkzeug.security import generate_password_hash

from app.repositories import user_repository
from app.services import audit_service
from app.services.exceptions import LastAdministratorError, NotFoundError, PermissionDeniedError
from app.utils.database import db, transaction


def change_role(target_id, actor_id, role, context):
    if target_id == actor_id:
        raise PermissionDeniedError("Use another administrator account to change your own role.")
    with transaction() as cursor:
        database = db.using(cursor)
        user = _require_user(target_id, database)
        if user.is_admin and role != "admin":
            _guard_last_admin(user.id, database)
        user_repository.update_role(user.id, role, database=database)
        audit_service.record(
            "role_updated", f"{user.email} role changed to {role}", context, database
        )
    return user


def set_banned(target_id, actor_id, banned, context):
    if target_id == actor_id and banned:
        raise PermissionDeniedError("You cannot ban your own account.")
    with transaction() as cursor:
        database = db.using(cursor)
        user = _require_user(target_id, database)
        if banned and user.is_admin:
            _guard_last_admin(user.id, database)
        user_repository.set_banned(user.id, banned, database=database)
        action = "user_banned" if banned else "user_unbanned"
        audit_service.record(
            action,
            f"{user.email} was {'banned' if banned else 'unbanned'}",
            context,
            database,
        )
    return user


def reset_password(target_id, actor_id, password, context):
    if target_id == actor_id:
        raise PermissionDeniedError("Use your own Security page to change your password.")
    with transaction() as cursor:
        database = db.using(cursor)
        user = _require_user(target_id, database)
        user_repository.update_password(
            user.id,
            generate_password_hash(password),
            user.auth_version + 1,
            reset_failures=True,
            database=database,
        )
        audit_service.record(
            "admin_password_reset", f"Password reset for {user.email}", context, database
        )
    return user


def delete_user(target_id, actor_id, actor_email, context):
    if target_id == actor_id:
        raise PermissionDeniedError("You cannot delete your own account.")
    with transaction() as cursor:
        database = db.using(cursor)
        user = _require_user(target_id, database)
        if user.is_admin:
            _guard_last_admin(user.id, database)
        user_repository.delete(user.id, cursor=cursor)
        audit_service.record(
            "user_deleted",
            f"{user.email} was deleted by {actor_email}",
            context,
            database,
        )
    return user


def _require_user(user_id, database):
    user = user_repository.find_by_id(user_id, database=database)
    if not user:
        raise NotFoundError("User not found.")
    return user


def _guard_last_admin(user_id, database):
    if user_repository.count_other_active_admins(user_id, database=database) == 0:
        raise LastAdministratorError("Keep at least one active administrator account.")
