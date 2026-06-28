from app import create_app
from utils.db import fetch_scalar

app = create_app()

with app.app_context():
    print("Database connected successfully:", fetch_scalar("SELECT 1", default=0))
