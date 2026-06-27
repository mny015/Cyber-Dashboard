from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    Limiter = None

    def get_remote_address():
        return "127.0.0.1"

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address) if Limiter else None

login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

from app.models.user import User  # noqa: E402,F401
from app.models.category import Category  # noqa: E402,F401
from app.models.topic import Topic  # noqa: E402,F401
from app.models.contact import Contact  # noqa: E402,F401
from app.models.audit_log import AuditLog  # noqa: E402,F401
