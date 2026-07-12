"""Dashboard URL mappings."""

from flask import Blueprint

from app.controllers import dashboard_controller


dashboard_bp = Blueprint("dashboard", __name__)
dashboard_bp.add_url_rule("/", endpoint="index", view_func=dashboard_controller.index, methods=["GET"])
dashboard_bp.add_url_rule(
    "/dashboard", endpoint="dashboard", view_func=dashboard_controller.dashboard, methods=["GET"]
)
dashboard_bp.add_url_rule(
    "/user/dashboard",
    endpoint="user_dashboard",
    view_func=dashboard_controller.user_dashboard,
    methods=["GET"],
)
dashboard_bp.add_url_rule(
    "/admin/dashboard",
    endpoint="admin_dashboard",
    view_func=dashboard_controller.admin_dashboard,
    methods=["GET"],
)
