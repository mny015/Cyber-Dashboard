from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

from app.models.user import User  # noqa: E402,F401
from app.models.category import Category  # noqa: E402,F401
from app.models.topic import Topic  # noqa: E402,F401
from app.models.contact import Contact  # noqa: E402,F401
