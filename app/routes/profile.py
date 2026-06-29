import hashlib
import os

from flask import Blueprint, Response, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.forms.profile import ProfileForm
from utils.audit import log_audit
from utils.db import execute, fetch_one

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

ALLOWED_IMAGE_TYPES = {
    "jpeg": {"extensions": {".jpg", ".jpeg"}, "mimes": {"image/jpeg"}},
    "png": {"extensions": {".png"}, "mimes": {"image/png"}},
    "gif": {"extensions": {".gif"}, "mimes": {"image/gif"}},
    "webp": {"extensions": {".webp"}, "mimes": {"image/webp"}},
}
EXTENSION_BY_TYPE = {
    "jpeg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "webp": ".webp",
}


@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def edit():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing = fetch_one(
            "SELECT id FROM users WHERE email = %s AND id <> %s",
            (email, current_user.id),
        )
        if existing:
            flash("That email is already used by another account.", "danger")
            return render_template("profile/edit.html", form=form)

        image_update = None
        if form.profile_image.data and form.profile_image.data.filename:
            is_valid, message = validate_profile_image(form.profile_image.data)
            if not is_valid:
                flash(message, "danger")
                return render_template("profile/edit.html", form=form)
            image_update = build_profile_image_record(form.profile_image.data)

        update_profile(form, email, image_update)
        log_audit("profile_updated", "User updated profile information")
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile.edit"))

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/picture/<image_hash>")
@login_required
def picture(image_hash):
    if image_hash != current_user.profile_image:
        abort(404)

    row = fetch_one(
        """
        SELECT profile_image_data, profile_image_mime, profile_image_size
        FROM users
        WHERE id = %s AND profile_image = %s
        """,
        (current_user.id, image_hash),
    )
    if not row or not row["profile_image_data"]:
        abort(404)

    return Response(
        row["profile_image_data"],
        mimetype=row["profile_image_mime"],
        headers={
            "Content-Length": str(row["profile_image_size"] or len(row["profile_image_data"])),
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=300",
        },
    )


def update_profile(form, email, image_update):
    params = [
        form.display_name.data.strip(),
        email,
        form.profile_bio.data.strip() if form.profile_bio.data else "",
    ]

    if image_update:
        execute(
            """
            UPDATE users
            SET display_name = %s, email = %s, profile_bio = %s,
                profile_image = %s, profile_image_data = %s, profile_image_mime = %s,
                profile_image_size = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (
                *params,
                image_update["hash"],
                image_update["data"],
                image_update["mime"],
                image_update["size"],
                current_user.id,
            ),
        )
        return

    execute(
        """
        UPDATE users
        SET display_name = %s, email = %s, profile_bio = %s, updated_at = NOW()
        WHERE id = %s
        """,
        (*params, current_user.id),
    )


def build_profile_image_record(file_storage):
    image_bytes = read_file_bytes(file_storage)
    image_type = detect_image_type_from_bytes(image_bytes)
    digest = hashlib.sha256(image_bytes).hexdigest()
    return {
        "hash": digest,
        "data": image_bytes,
        "mime": next(iter(ALLOWED_IMAGE_TYPES[image_type]["mimes"])),
        "size": len(image_bytes),
    }


def validate_profile_image(file_storage):
    if not isinstance(file_storage, FileStorage) or not file_storage.filename:
        return False, "Choose an image file to upload."

    safe_name = secure_filename(file_storage.filename)
    extension = os.path.splitext(safe_name)[1].lower()
    if not extension:
        return False, "Profile picture must have an image extension."

    image_bytes = read_file_bytes(file_storage)
    image_type = detect_image_type_from_bytes(image_bytes)
    if image_type not in ALLOWED_IMAGE_TYPES:
        return False, "Only clean JPG, PNG, GIF, or WEBP images are allowed."

    allowed = ALLOWED_IMAGE_TYPES[image_type]
    if extension not in allowed["extensions"]:
        return False, "Image file extension does not match the uploaded image type."

    if file_storage.mimetype not in allowed["mimes"]:
        return False, "Image MIME type does not match the uploaded image."

    return True, ""


def read_file_bytes(file_storage):
    position = file_storage.stream.tell()
    file_bytes = file_storage.stream.read()
    file_storage.stream.seek(position)
    return file_bytes


def detect_image_type(file_storage):
    return detect_image_type_from_bytes(read_file_bytes(file_storage))


def detect_image_type_from_bytes(file_bytes):
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
