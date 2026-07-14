"""Environment-driven configuration for every application runtime."""

import os
import base64
import binascii
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


def require_env(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Copy .env.example to .env and set it."
        )
    return value.strip()


def require_int_env(name):
    value = require_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a whole number.") from exc


class BaseConfig:
    """Settings shared by development, testing, and production."""

    SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

    DB_HOST = os.getenv("DB_HOST", "").strip()
    DB_PORT = os.getenv("DB_PORT", "").strip()
    DB_USER = os.getenv("DB_USER", "").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip()
    DB_NAME = os.getenv("DB_NAME", "").strip()
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4").strip() or "utf8mb4"
    DB_POOL_SIZE = os.getenv("DB_POOL_SIZE", "5").strip()
    DB_POOL_TIMEOUT = os.getenv("DB_POOL_TIMEOUT", "5").strip()

    MFA_ENCRYPTION_KEY = os.getenv("MFA_ENCRYPTION_KEY", "").strip()
    REAUTHENTICATION_MAX_AGE = os.getenv("REAUTHENTICATION_MAX_AGE", "600").strip()
    TRUSTED_PROXY_HOPS = os.getenv("TRUSTED_PROXY_HOPS", "0").strip()

    WTF_CSRF_ENABLED = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = False

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    LOG_FILE = os.getenv("LOG_FILE", "instance/cyber_dashboard.log")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    PROFILE_IMAGE_MAX_BYTES = os.getenv(
        "PROFILE_IMAGE_MAX_BYTES", str(2 * 1024 * 1024)
    ).strip()

    TALISMAN_FORCE_HTTPS = False
    TALISMAN_STRICT_TRANSPORT_SECURITY = True

    TESTING = False
    DEBUG = False

    @classmethod
    def validate(cls):
        required = {
            "SECRET_KEY": cls.SECRET_KEY,
            "DB_HOST": cls.DB_HOST,
            "DB_PORT": cls.DB_PORT,
            "DB_USER": cls.DB_USER,
            "DB_PASSWORD": cls.DB_PASSWORD,
            "DB_NAME": cls.DB_NAME,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            joined_names = ", ".join(sorted(missing))
            raise RuntimeError(
                f"Missing required environment variables: {joined_names}. "
                "Copy .env.example to .env and set them."
            )

        try:
            cls.DB_PORT = int(cls.DB_PORT)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("DB_PORT must be a whole number.") from exc
        try:
            cls.DB_POOL_SIZE = int(cls.DB_POOL_SIZE)
            cls.DB_POOL_TIMEOUT = float(cls.DB_POOL_TIMEOUT)
            cls.REAUTHENTICATION_MAX_AGE = int(cls.REAUTHENTICATION_MAX_AGE)
            cls.TRUSTED_PROXY_HOPS = int(cls.TRUSTED_PROXY_HOPS)
            cls.PROFILE_IMAGE_MAX_BYTES = int(cls.PROFILE_IMAGE_MAX_BYTES)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Database and security numeric settings must be numbers.") from exc
        if cls.DB_POOL_SIZE < 1 or cls.DB_POOL_TIMEOUT <= 0:
            raise RuntimeError("DB_POOL_SIZE and DB_POOL_TIMEOUT must be positive.")
        if cls.REAUTHENTICATION_MAX_AGE < 60:
            raise RuntimeError("REAUTHENTICATION_MAX_AGE must be at least 60 seconds.")
        if cls.TRUSTED_PROXY_HOPS < 0:
            raise RuntimeError("TRUSTED_PROXY_HOPS cannot be negative.")
        if cls.PROFILE_IMAGE_MAX_BYTES < 1024:
            raise RuntimeError("PROFILE_IMAGE_MAX_BYTES must be at least 1024 bytes.")


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""

    DEBUG = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"


class TestingConfig(BaseConfig):
    """Automated test configuration."""

    TESTING = True
    DEBUG = False
    SESSION_COOKIE_SECURE = False
    TALISMAN_FORCE_HTTPS = False


class ProductionConfig(BaseConfig):
    """Hardened deployment configuration."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    TALISMAN_FORCE_HTTPS = True

    @classmethod
    def validate(cls):
        super().validate()
        if len(cls.SECRET_KEY) < 32 or cls.SECRET_KEY.lower().startswith("replace-with"):
            raise RuntimeError("Production SECRET_KEY must be a non-placeholder value of at least 32 characters.")
        if cls.DB_PASSWORD.lower().startswith("replace-with"):
            raise RuntimeError("Production DB_PASSWORD must not be a placeholder value.")
        try:
            decoded_mfa_key = base64.urlsafe_b64decode(cls.MFA_ENCRYPTION_KEY.encode("ascii"))
        except (ValueError, UnicodeError, binascii.Error):
            decoded_mfa_key = b""
        if len(decoded_mfa_key) != 32:
            raise RuntimeError(
                "Production MFA_ENCRYPTION_KEY must be a Fernet key stored in the environment."
            )
        if cls.RATELIMIT_STORAGE_URI.strip().lower() == "memory://":
            raise RuntimeError(
                "Production RATELIMIT_STORAGE_URI must use shared storage such as Redis."
            )


CONFIGURATIONS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    config_name = (name or os.getenv("APP_ENV", "development")).strip().lower()
    try:
        config_class = CONFIGURATIONS[config_name]
    except KeyError as exc:
        choices = ", ".join(sorted(CONFIGURATIONS))
        raise RuntimeError(f"Unknown APP_ENV '{config_name}'. Choose one of: {choices}.") from exc
    config_class.validate()
    return config_class


# Compatibility alias for scripts and the existing database helper.
Config = get_config()
