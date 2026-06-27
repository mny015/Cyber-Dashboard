import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

from config import Config
from app.models import csrf, db, limiter, login_manager, migrate
from app.routes import register_blueprints
from utils.helpers import format_date

try:
    from flask_talisman import Talisman
except ImportError:
    Talisman = None


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    if limiter:
        limiter.init_app(app)

    configure_security_headers(app)
    configure_logging(app)

    register_blueprints(app)

    app.jinja_env.filters["format_date"] = format_date

    register_error_handlers(app)

    return app


def configure_security_headers(app):
    if not Talisman:
        return

    csp = {
        "default-src": "'self'",
        "style-src": ["'self'", "'unsafe-inline'"],
        "script-src": ["'self'"],
        "img-src": ["'self'", "data:"],
    }
    Talisman(
        app,
        content_security_policy=csp,
        force_https=False,
        frame_options="DENY",
        strict_transport_security=True,
    )


def configure_logging(app):
    os.makedirs(os.path.dirname(app.config["LOG_FILE"]), exist_ok=True)
    handler = RotatingFileHandler(app.config["LOG_FILE"], maxBytes=200000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def register_error_handlers(app):
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
