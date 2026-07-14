"""One-time rotation of legacy plaintext TOTP secrets into encrypted storage."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.models import User
from app.utils.database import db, transaction
from app.utils.security import encrypt_mfa_secret, is_encrypted_mfa_secret


def rotate_legacy_mfa_secrets():
    rows = (
        db.table(User.TABLE_NAME)
        .select("id", "mfa_secret")
        .where_not_null("mfa_secret")
        .all()
    )
    legacy_rows = [row for row in rows if not is_encrypted_mfa_secret(row["mfa_secret"])]
    if not legacy_rows:
        return 0

    with transaction() as cursor:
        database = db.using(cursor)
        for row in legacy_rows:
            database.table(User.TABLE_NAME).where("id", "=", int(row["id"])).update(
                {"mfa_secret": encrypt_mfa_secret(row["mfa_secret"])}
            )
    return len(legacy_rows)


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        rotated = rotate_legacy_mfa_secrets()
    print(f"Encrypted {rotated} legacy MFA secret(s).")
