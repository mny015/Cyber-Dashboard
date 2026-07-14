"""Compatibility adapter for the centralized upload validation policy."""

from app.utils.uploads import (
    UploadValidationError,
    detect_image_type,
    validate_profile_image,
)


def validate(file_storage):
    try:
        validate_profile_image(file_storage)
    except UploadValidationError as exc:
        return False, str(exc)
    return True, ""


def build_record(file_storage):
    return validate_profile_image(file_storage).to_profile_image()


def read_bytes(file_storage):
    position = file_storage.stream.tell()
    file_bytes = file_storage.stream.read()
    file_storage.stream.seek(position)
    return file_bytes


def detect_type(file_bytes):
    return detect_image_type(file_bytes)
