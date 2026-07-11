"""User persistence operations used outside request controllers."""

from app.models.user import User
from app.utils.database import db


def find_by_id(user_id):
    try:
        normalized_id = int(user_id)
    except (TypeError, ValueError):
        return None
    row = db.table(User.TABLE_NAME).where("id", "=", normalized_id).first()
    return User.from_row(row)
