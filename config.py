import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def require_env(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}. Copy .env.example to .env and set it.")
    return value.strip()


def require_int_env(name):
    value = require_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a whole number.") from exc


class Config:
    SECRET_KEY = require_env("SECRET_KEY")

    DB_HOST = require_env("DB_HOST")
    DB_PORT = require_int_env("DB_PORT")
    DB_USER = require_env("DB_USER")
    DB_PASSWORD = require_env("DB_PASSWORD")
    DB_NAME = require_env("DB_NAME")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

    WTF_CSRF_ENABLED = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    LOG_FILE = os.getenv("LOG_FILE", "instance/cyber_dashboard.log")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
