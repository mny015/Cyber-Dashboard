from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import login_manager
from utils.db import fetch_one


class User(UserMixin):
    def __init__(
        self,
        id=None,
        email="",
        password_hash="",
        display_name="",
        role="user",
        is_banned=False,
        mfa_secret=None,
        mfa_enabled=False,
        auth_version=0,
        failed_login_count=0,
        last_failed_login_at=None,
        locked_until=None,
        profile_bio="",
        profile_image="",
        created_at=None,
        updated_at=None,
        **extra,
    ):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.display_name = display_name
        self.role = role
        self.is_banned = bool(is_banned)
        self.mfa_secret = mfa_secret
        self.mfa_enabled = bool(mfa_enabled)
        self.auth_version = int(auth_version or 0)
        self.failed_login_count = int(failed_login_count or 0)
        self.last_failed_login_at = last_failed_login_at
        self.locked_until = locked_until
        self.profile_bio = profile_bio or ""
        self.profile_image = profile_image or ""
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(**row)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id):
    row = fetch_one("SELECT * FROM users WHERE id = %s", (int(user_id),))
    return User.from_row(row)
