"""Whitelist and inspect profile image uploads before database storage."""

import hashlib
import os

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.models import ProfileImage


ALLOWED_IMAGE_TYPES = {
    "jpeg": {"extensions": {".jpg", ".jpeg"}, "mimes": {"image/jpeg"}},
    "png": {"extensions": {".png"}, "mimes": {"image/png"}},
    "gif": {"extensions": {".gif"}, "mimes": {"image/gif"}},
    "webp": {"extensions": {".webp"}, "mimes": {"image/webp"}},
}


def validate(file_storage):
    if not isinstance(file_storage, FileStorage) or not file_storage.filename:
        return False, "Choose an image file to upload."
    extension = os.path.splitext(secure_filename(file_storage.filename))[1].lower()
    if not extension:
        return False, "Profile picture must have an image extension."

    image_type = detect_type(read_bytes(file_storage))
    if image_type not in ALLOWED_IMAGE_TYPES:
        return False, "Only clean JPG, PNG, GIF, or WEBP images are allowed."
    allowed = ALLOWED_IMAGE_TYPES[image_type]
    if extension not in allowed["extensions"]:
        return False, "Image file extension does not match the uploaded image type."
    if file_storage.mimetype not in allowed["mimes"]:
        return False, "Image MIME type does not match the uploaded image."
    return True, ""


def build_record(file_storage):
    image_bytes = read_bytes(file_storage)
    image_type = detect_type(image_bytes)
    return ProfileImage(
        image_hash=hashlib.sha256(image_bytes).hexdigest(),
        image_data=image_bytes,
        mime_type=next(iter(ALLOWED_IMAGE_TYPES[image_type]["mimes"])),
        byte_size=len(image_bytes),
    )


def read_bytes(file_storage):
    position = file_storage.stream.tell()
    file_bytes = file_storage.stream.read()
    file_storage.stream.seek(position)
    return file_bytes


def detect_type(file_bytes):
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
