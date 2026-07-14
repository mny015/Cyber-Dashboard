"""Authentication URL mappings."""

from flask import Blueprint

from app.controllers import auth_controller

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
auth_bp.add_url_rule(
    "/register", endpoint="register", view_func=auth_controller.register, methods=["GET", "POST"]
)
auth_bp.add_url_rule(
    "/login", endpoint="login", view_func=auth_controller.login, methods=["GET", "POST"]
)
auth_bp.add_url_rule(
    "/mfa/verify",
    endpoint="verify_mfa",
    view_func=auth_controller.verify_mfa,
    methods=["GET", "POST"],
)
auth_bp.add_url_rule(
    "/logout", endpoint="logout", view_func=auth_controller.logout, methods=["POST"]
)
auth_bp.add_url_rule(
    "/profile/mfa",
    endpoint="setup_mfa",
    view_func=auth_controller.setup_mfa,
    methods=["GET", "POST"],
)
auth_bp.add_url_rule(
    "/profile/mfa/qr", endpoint="mfa_qr", view_func=auth_controller.mfa_qr, methods=["GET"]
)
auth_bp.add_url_rule(
    "/profile/password",
    endpoint="change_password",
    view_func=auth_controller.change_password,
    methods=["POST"],
)
auth_bp.add_url_rule(
    "/reconfirm",
    endpoint="reconfirm",
    view_func=auth_controller.reconfirm,
    methods=["GET", "POST"],
)
