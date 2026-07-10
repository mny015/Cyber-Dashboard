from flask import Blueprint, render_template, send_file
from flask_login import current_user, login_required

from utils.audit import log_audit
from utils.db import fetch_all, fetch_one
from utils.decorators import admin_required
from utils.export_utils import csv_zip_bytes, export_filename, json_bytes

backup_bp = Blueprint("backup", __name__, url_prefix="/backup")


@backup_bp.route("/")
@login_required
def index():
    return render_template("backup/index.html")


@backup_bp.route("/personal.json")
@login_required
def personal_json():
    data = _personal_data(current_user.id)
    log_audit("personal_backup_exported", "Exported personal data as JSON")
    return send_file(
        json_bytes(data),
        mimetype="application/json",
        as_attachment=True,
        download_name=export_filename("personal", "json"),
    )


@backup_bp.route("/personal.zip")
@login_required
def personal_csv():
    data = _personal_data(current_user.id)
    log_audit("personal_backup_exported", "Exported personal data as CSV archive")
    return send_file(
        csv_zip_bytes(data),
        mimetype="application/zip",
        as_attachment=True,
        download_name=export_filename("personal", "zip"),
    )


@backup_bp.route("/admin.json")
@login_required
@admin_required
def admin_json():
    data = _admin_data(current_user.id)
    log_audit("admin_backup_exported", "Exported privacy-aware system data as JSON")
    return send_file(
        json_bytes(data),
        mimetype="application/json",
        as_attachment=True,
        download_name=export_filename("admin", "json"),
    )


@backup_bp.route("/admin.zip")
@login_required
@admin_required
def admin_csv():
    data = _admin_data(current_user.id)
    log_audit("admin_backup_exported", "Exported privacy-aware system data as CSV archive")
    return send_file(
        csv_zip_bytes(data),
        mimetype="application/zip",
        as_attachment=True,
        download_name=export_filename("admin", "zip"),
    )


def _personal_data(user_id):
    account = fetch_one(
        """
        SELECT id, email, display_name, role, is_banned, mfa_enabled,
               profile_bio, created_at, updated_at
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )
    return {
        "account": [account] if account else [],
        "categories": fetch_all(
            """
            SELECT id, name, description, color, is_deleted, created_at, updated_at
            FROM categories
            WHERE owner_id = %s
            ORDER BY id
            """,
            (user_id,),
        ),
        "topics": fetch_all(
            """
            SELECT id, title, slug, description, status, priority, notes,
                   is_deleted, category_id, created_at, updated_at
            FROM topics
            WHERE owner_id = %s
            ORDER BY id
            """,
            (user_id,),
        ),
        "notes": fetch_all(
            """
            SELECT id, title, body, topic_id, is_deleted, created_at, updated_at
            FROM notes
            WHERE owner_id = %s
            ORDER BY id
            """,
            (user_id,),
        ),
        "contacts": fetch_all(
            """
            SELECT id, name, email, phone, notes, is_deleted, created_at, updated_at
            FROM contacts
            WHERE owner_id = %s
            ORDER BY id
            """,
            (user_id,),
        ),
        "labs": fetch_all(
            """
            SELECT labs.id, labs.name, platforms.name AS platform, labs.url,
                   labs.notes, labs.topic_id, labs.visibility, labs.is_deleted,
                   labs.created_at, labs.updated_at
            FROM lab_references AS labs
            JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
            WHERE labs.owner_id = %s
            ORDER BY labs.id
            """,
            (user_id,),
        ),
        "lab_completions": fetch_all(
            """
            SELECT completions.id, completions.lab_id, labs.name AS lab_name,
                   completions.completed_at
            FROM lab_completions AS completions
            JOIN lab_references AS labs ON labs.id = completions.lab_id
            WHERE completions.user_id = %s
            ORDER BY completions.id
            """,
            (user_id,),
        ),
        "note_access_requests": fetch_all(
            """
            SELECT requests.id, requests.topic_id, requests.note_id,
                   COALESCE(admins.display_name, 'Deleted administrator') AS requested_by,
                   requests.status,
                   requests.requested_at, requests.responded_at
            FROM note_access_requests AS requests
            JOIN topics ON topics.id = requests.topic_id
            LEFT JOIN users AS admins ON admins.id = requests.requester_admin_id
            WHERE topics.owner_id = %s
            ORDER BY requests.id
            """,
            (user_id,),
        ),
    }


def _admin_data(admin_id):
    data = _personal_data(admin_id)
    data.update(
        {
            "system_users": fetch_all(
                """
                SELECT id, email, display_name, role, is_banned, mfa_enabled,
                       created_at, updated_at
                FROM users
                ORDER BY id
                """
            ),
            "system_categories": fetch_all(
                """
                SELECT categories.id, categories.name, categories.color,
                       categories.is_deleted, categories.created_at,
                       users.id AS owner_id, users.display_name AS owner_name
                FROM categories
                JOIN users ON users.id = categories.owner_id
                ORDER BY categories.id
                """
            ),
            "system_topics": fetch_all(
                """
                SELECT topics.id, topics.title, topics.status, topics.priority,
                       topics.is_deleted, topics.category_id, topics.created_at,
                       topics.updated_at, users.id AS owner_id,
                       users.display_name AS owner_name
                FROM topics
                JOIN users ON users.id = topics.owner_id
                ORDER BY topics.id
                """
            ),
            "shared_labs": fetch_all(
                """
                SELECT labs.id, labs.name, platforms.name AS platform, labs.url,
                       labs.visibility, labs.is_deleted, labs.created_at,
                       users.id AS owner_id, users.display_name AS owner_name
                FROM lab_references AS labs
                JOIN lab_platforms AS platforms ON platforms.id = labs.platform_id
                JOIN users ON users.id = labs.owner_id
                WHERE labs.visibility = 'public'
                ORDER BY labs.id
                """
            ),
            "approved_notes": fetch_all(
                """
                SELECT notes.id, notes.title, notes.body, notes.topic_id,
                       notes.owner_id, notes.is_deleted, notes.created_at,
                       notes.updated_at
                FROM notes
                JOIN note_access_requests AS requests
                  ON requests.topic_id = notes.topic_id
                 AND (requests.note_id IS NULL OR requests.note_id = notes.id)
                WHERE requests.requester_admin_id = %s
                  AND requests.status = 'approved'
                ORDER BY notes.id
                """,
                (admin_id,),
            ),
            "audit_logs": fetch_all(
                """
                SELECT audit_logs.id, audit_logs.action, audit_logs.details,
                       audit_logs.user_id, users.display_name AS user_name,
                       audit_logs.created_at
                FROM audit_logs
                LEFT JOIN users ON users.id = audit_logs.user_id
                ORDER BY audit_logs.id
                """
            ),
        }
    )
    return data
