"""WSGI entry point for production servers."""

import os

os.environ.setdefault("APP_ENV", "production")

from app import create_app


app = create_app("production")
