"""Strict profile-image validation and content-addressed filename generation."""

import hashlib
import os
from dataclasses import dataclass

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from wtforms.validators import ValidationError

from app.models import ProfileImage

ALLOWED_IMAGE_TYPES = {
    "jpeg": {"extensions": {".jpg", ".jpeg"}, "mime": "image/jpeg"},
    "png": {"extensions": {".png"}, "mime": "image/png"},
    "gif": {"extensions": {".gif"}, "mime": "image/gif"},
    "webp": {"extensions": {".webp"}, "mime": "image/webp"},
}


class UploadValidationError(ValueError):
    """Raised when an uploaded file fails a declared validation policy."""


@dataclass(frozen=True, slots=True)
class ValidatedImageUpload:
    data: bytes
    image_type: str
    extension: str
    mime_type: str
    image_hash: str

    @property
    def byte_size(self):
        return len(self.data)

    @property
    def generated_filename(self):
        return f"{self.image_hash}{self.extension}"

    def to_profile_image(self):
        return ProfileImage(
            image_hash=self.image_hash,
            image_data=self.data,
            mime_type=self.mime_type,
            byte_size=self.byte_size,
        )


class ProfileImageUploadValidator:
    """Flask-WTF validator that caches one inspected upload on the field."""

    def __call__(self, form, field):
        upload = field.data
        if not isinstance(upload, FileStorage) or not upload.filename:
            field.validated_upload = None
            return
        try:
            field.validated_upload = validate_profile_image(upload)
        except UploadValidationError as exc:
            raise ValidationError(str(exc)) from exc


def validate_profile_image(file_storage, max_bytes=None):
    if not isinstance(file_storage, FileStorage) or not file_storage.filename:
        raise UploadValidationError("Choose an image file to upload.")

    safe_name = secure_filename(file_storage.filename)
    extension = os.path.splitext(safe_name)[1].lower()
    if not extension:
        raise UploadValidationError("Profile picture must have an image extension.")

    maximum = int(
        max_bytes
        if max_bytes is not None
        else current_app.config.get("PROFILE_IMAGE_MAX_BYTES", 2 * 1024 * 1024)
    )
    file_bytes = _read_bounded(file_storage, maximum)
    image_type = detect_image_type(file_bytes)
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise UploadValidationError("Only valid JPG, PNG, GIF, or WEBP images are allowed.")

    policy = ALLOWED_IMAGE_TYPES[image_type]
    if extension not in policy["extensions"]:
        raise UploadValidationError("Image extension does not match its file signature.")
    supplied_mime = (file_storage.mimetype or "").split(";", 1)[0].strip().lower()
    if supplied_mime != policy["mime"]:
        raise UploadValidationError("Image MIME type does not match its file signature.")

    return ValidatedImageUpload(
        data=file_bytes,
        image_type=image_type,
        extension=extension,
        mime_type=policy["mime"],
        image_hash=hashlib.sha256(file_bytes).hexdigest(),
    )


def detect_image_type(file_bytes):
    if file_bytes.startswith(b"\xff\xd8\xff") and file_bytes.endswith(b"\xff\xd9"):
        return "jpeg"
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n") and file_bytes.endswith(
        b"\x00\x00\x00\x00IEND\xaeB\x60\x82"
    ):
        return "png"
    if file_bytes.startswith((b"GIF87a", b"GIF89a")) and file_bytes.endswith(b";"):
        return "gif"
    if (
        len(file_bytes) >= 12
        and file_bytes.startswith(b"RIFF")
        and file_bytes[8:12] == b"WEBP"
        and int.from_bytes(file_bytes[4:8], "little") + 8 == len(file_bytes)
    ):
        return "webp"
    return None


def _read_bounded(file_storage, maximum):
    if maximum < 1:
        raise UploadValidationError("Upload size configuration is invalid.")
    stream = file_storage.stream
    try:
        position = stream.tell()
    except (AttributeError, OSError):
        position = None
    file_bytes = stream.read(maximum + 1)
    try:
        stream.seek(position if position is not None else 0)
    except (AttributeError, OSError):
        pass
    if not file_bytes:
        raise UploadValidationError("The uploaded image is empty.")
    if len(file_bytes) > maximum:
        raise UploadValidationError(f"Profile picture must be no larger than {maximum // 1024} KB.")
    return file_bytes
