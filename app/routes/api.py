from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "Cyber Dashboard API is online"})
