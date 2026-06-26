from flask import Flask, render_template

from config import Config
from app.models import db, migrate, login_manager
from app.routes import register_blueprints
from utils.helpers import format_date


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    register_blueprints(app)

    app.jinja_env.filters["format_date"] = format_date

    register_error_handlers(app)

    return app


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html", error=error), 500
