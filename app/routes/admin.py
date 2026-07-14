"""Administrator URL mappings."""

from flask import Blueprint

from app.controllers import admin_controller

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
admin_bp.add_url_rule("/users", endpoint="users", view_func=admin_controller.users, methods=["GET"])
admin_bp.add_url_rule(
    "/topics", endpoint="topic_summaries", view_func=admin_controller.topic_summaries, methods=["GET"]
)
admin_bp.add_url_rule(
    "/topics/<int:topic_id>/request-notes",
    endpoint="request_topic_notes",
    view_func=admin_controller.request_topic_notes,
    methods=["POST"],
)
admin_bp.add_url_rule(
    "/note-requests",
    endpoint="note_requests",
    view_func=admin_controller.note_requests,
    methods=["GET"],
)
admin_bp.add_url_rule(
    "/note-requests/<int:request_id>/note",
    endpoint="approved_note",
    view_func=admin_controller.approved_note,
    methods=["GET"],
)
admin_bp.add_url_rule(
    "/categories",
    endpoint="category_summaries",
    view_func=admin_controller.category_summaries,
    methods=["GET"],
)
admin_bp.add_url_rule(
    "/users/<int:user_id>/role",
    endpoint="update_role",
    view_func=admin_controller.update_role,
    methods=["POST"],
)
admin_bp.add_url_rule(
    "/users/<int:user_id>/ban",
    endpoint="ban_user",
    view_func=admin_controller.ban_user,
    methods=["POST"],
)
admin_bp.add_url_rule(
    "/users/<int:user_id>/unban",
    endpoint="unban_user",
    view_func=admin_controller.unban_user,
    methods=["POST"],
)
admin_bp.add_url_rule(
    "/users/<int:user_id>/password",
    endpoint="reset_user_password",
    view_func=admin_controller.reset_user_password,
    methods=["POST"],
)
admin_bp.add_url_rule(
    "/users/<int:user_id>/delete",
    endpoint="delete_user",
    view_func=admin_controller.delete_user,
    methods=["POST"],
)
admin_bp.add_url_rule(
    "/audit-logs", endpoint="audit_logs", view_func=admin_controller.audit_logs, methods=["GET"]
)
