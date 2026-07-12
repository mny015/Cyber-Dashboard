"""HTTP handlers for the lightweight JSON API."""

from flask import jsonify


def ping():
    return jsonify({"status": "ok", "message": "Cyber Dashboard API is online"})
