import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, session
from flask_login import current_user, logout_user

from app.extensions import init_extensions, login_manager
from app.repositories import user_repository
from app.routes import register_blueprints
from app.utils.database import (
    DatabaseConnectionError,
    DatabaseError,
    init_database,
)
from app.utils.datetime_helpers import format_date
from app.utils.security import configure_trusted_proxy
from config import get_config


@login_manager.user_loader
def load_authenticated_user(user_id):
    return user_repository.find_by_id(user_id)


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    configure_trusted_proxy(app)
    init_extensions(app)
    init_database(app)

    configure_logging(app)

    register_blueprints(app)
    register_session_checks(app)

    app.jinja_env.filters["format_date"] = format_date

    register_error_handlers(app)

    return app


def register_session_checks(app):
    @app.before_request
    def reject_stale_session():
        if not current_user.is_authenticated:
            return
        session_version = session.get("auth_version")
        if session_version != current_user.auth_version:
            logout_user()
            session.clear()


def configure_logging(app):
    os.makedirs(os.path.dirname(app.config["LOG_FILE"]), exist_ok=True)
    handler = RotatingFileHandler(app.config["LOG_FILE"], maxBytes=200000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def register_error_handlers(app):
    @app.errorhandler(DatabaseConnectionError)
    def database_unavailable(error):
        app.logger.error("Database connection unavailable: %s", type(error).__name__)
        return render_template("errors/500.html"), 503

    @app.errorhandler(DatabaseError)
    def database_failure(error):
        app.logger.error("Database operation failed: %s", type(error).__name__)
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Unhandled server error: %s", error)
        return render_template("errors/500.html", error=error), 500
