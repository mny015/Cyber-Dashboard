"""Flask extension instances and application-factory initialization."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_wtf import CSRFProtect


CONTENT_SECURITY_POLICY = {
    "default-src": "'self'",
    "style-src": ["'self'", "'unsafe-inline'"],
    "script-src": ["'self'"],
    "img-src": ["'self'", "data:"],
}

login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


def init_extensions(app):
    """Bind the shared extension instances to one Flask application."""
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    talisman.init_app(
        app,
        content_security_policy=CONTENT_SECURITY_POLICY,
        force_https=app.config["TALISMAN_FORCE_HTTPS"],
        frame_options="DENY",
        strict_transport_security=app.config["TALISMAN_STRICT_TRANSPORT_SECURITY"],
    )


__all__ = ["csrf", "init_extensions", "limiter", "login_manager", "talisman"]
