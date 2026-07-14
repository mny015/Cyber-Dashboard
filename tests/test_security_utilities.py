"""Unit coverage for shared security and request utilities."""

from io import BytesIO

import pyotp
import pytest
from cryptography.fernet import Fernet
from flask import Flask
from werkzeug.datastructures import FileStorage
from werkzeug.middleware.proxy_fix import ProxyFix

from app.models import User
from app.utils.datetime_helpers import parse_datetime
from app.utils.pagination import normalize_pagination
from app.utils.redirects import is_safe_redirect_target, safe_local_path
from app.utils.security import (
    configure_trusted_proxy,
    decrypt_mfa_secret,
    encrypt_mfa_secret,
    get_client_address,
    hash_password,
    is_encrypted_mfa_secret,
    mark_reauthenticated,
    is_reauthentication_fresh,
    verify_password,
    verify_reauthentication,
)
from app.utils.uploads import UploadValidationError, validate_profile_image
from app.utils.validation import clean_text, is_valid_email, is_valid_phone, slugify


@pytest.fixture()
def utility_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="utility-test-secret",
        MFA_ENCRYPTION_KEY=Fernet.generate_key().decode("ascii"),
        PROFILE_IMAGE_MAX_BYTES=1024,
        REAUTHENTICATION_MAX_AGE=600,
        TRUSTED_PROXY_HOPS=0,
    )
    return app


def test_redirect_targets_must_remain_same_origin(utility_app):
    with utility_app.test_request_context("/", base_url="https://dashboard.test"):
        assert is_safe_redirect_target("/notes?page=2")
        assert safe_local_path("https://dashboard.test/topics#active") == "/topics#active"
        assert not is_safe_redirect_target("https://attacker.test/steal")
        assert not is_safe_redirect_target("//attacker.test/steal")
        assert not is_safe_redirect_target("\\attacker.test\\steal")


def test_raw_forwarded_for_is_ignored_without_trusted_proxy(utility_app):
    with utility_app.test_request_context(
        "/",
        headers={"X-Forwarded-For": "203.0.113.50"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    ):
        assert get_client_address() == "127.0.0.1"


def test_proxy_headers_are_enabled_only_with_explicit_hops():
    app = Flask(__name__)
    app.config["TRUSTED_PROXY_HOPS"] = 1

    configure_trusted_proxy(app)

    assert isinstance(app.wsgi_app, ProxyFix)


def test_mfa_secret_is_encrypted_and_decrypted(utility_app):
    with utility_app.app_context():
        protected = encrypt_mfa_secret("JBSWY3DPEHPK3PXP")

        assert is_encrypted_mfa_secret(protected)
        assert "JBSWY3DPEHPK3PXP" not in protected
        assert decrypt_mfa_secret(protected) == "JBSWY3DPEHPK3PXP"
        assert decrypt_mfa_secret("LEGACYPLAINTEXT") == "LEGACYPLAINTEXT"


def test_password_and_mfa_can_reconfirm_identity(utility_app):
    user = User(id=5, email="user@example.com", mfa_enabled=True)
    user.set_password("CorrectPassword123!")
    user.mfa_secret = pyotp.random_base32()

    assert verify_reauthentication(user, password="CorrectPassword123!")
    assert verify_reauthentication(user, mfa_token=pyotp.TOTP(user.mfa_secret).now())
    assert not verify_reauthentication(user, password="wrong")


def test_password_hashing_is_one_way_and_verifiable():
    password_hash = hash_password("CorrectPassword123!")

    assert "CorrectPassword123!" not in password_hash
    assert verify_password(password_hash, "CorrectPassword123!")
    assert not verify_password(password_hash, "wrong")


def test_recent_reauthentication_is_bound_to_auth_version(utility_app):
    user = User(id=8, auth_version=2)
    with utility_app.test_request_context("/"):
        mark_reauthenticated(user)
        assert is_reauthentication_fresh(user)
        user.auth_version = 3
        assert not is_reauthentication_fresh(user)


def test_upload_validation_checks_signature_mime_extension_size_and_hash(utility_app):
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\x00IEND\xaeB\x60\x82"
    )
    upload = FileStorage(
        stream=BytesIO(png_bytes), filename="profile.png", content_type="image/png"
    )
    with utility_app.app_context():
        validated = validate_profile_image(upload)

    assert validated.mime_type == "image/png"
    assert validated.generated_filename.endswith(".png")
    assert validated.image_hash in validated.generated_filename

    mismatched = FileStorage(
        stream=BytesIO(png_bytes), filename="profile.jpg", content_type="image/jpeg"
    )
    with utility_app.app_context(), pytest.raises(UploadValidationError, match="extension"):
        validate_profile_image(mismatched)

    oversized = FileStorage(
        stream=BytesIO(png_bytes), filename="profile.png", content_type="image/png"
    )
    with utility_app.app_context(), pytest.raises(UploadValidationError, match="no larger"):
        validate_profile_image(oversized, max_bytes=8)


def test_pagination_is_bounded_and_date_parsing_is_strict():
    pagination = normalize_pagination("-4", "500", max_per_page=100)

    assert pagination.page == 1
    assert pagination.per_page == 100
    assert pagination.offset == 0
    assert parse_datetime("2026-07-14T09:30").minute == 30
    with pytest.raises(ValueError):
        parse_datetime("next Tuesday")


def test_shared_text_validation_is_predictable():
    assert clean_text("  Focus  ") == "Focus"
    assert slugify("Broken Access Control!") == "broken-access-control"
    assert is_valid_email("user@example.com")
    assert not is_valid_email("not-an-email")
    assert is_valid_phone("+977 980-000-0000")
