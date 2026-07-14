"""API URL mappings."""

from flask import Blueprint

from app.controllers import api_controller

api_bp = Blueprint("api", __name__, url_prefix="/api")
api_bp.add_url_rule("/ping", endpoint="ping", view_func=api_controller.ping, methods=["GET"])
