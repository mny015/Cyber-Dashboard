from sqlalchemy import text

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    result = db.session.execute(text("SELECT 1"))
    print("Database connected successfully:", result.scalar())
