from urllib.parse import urlparse

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from utils.audit import log_audit
from utils.db import execute, fetch_all, fetch_one
from utils.helpers import clean_text

labs_bp = Blueprint("labs", __name__, url_prefix="/labs")

PLATFORMS = ["picoCTF", "TryHackMe", "Hack The Box", "PortSwigger", "Other"]


@labs_bp.route("/")
@login_required
def index():
    platform = clean_text(request.args.get("platform"))
    if platform:
        labs = fetch_all(
            """
            SELECT labs.*, topics.title AS topic_title,
                   owners.display_name AS owner_name, owners.role AS owner_role,
                   CASE WHEN completions.id IS NULL THEN 0 ELSE 1 END AS is_completed
            FROM lab_references AS labs
            JOIN users AS owners ON owners.id = labs.owner_id
            LEFT JOIN topics ON topics.id = labs.topic_id
            LEFT JOIN lab_completions AS completions
                   ON completions.lab_id = labs.id AND completions.user_id = %s
            WHERE labs.is_deleted = 0
              AND (labs.owner_id = %s OR (labs.visibility = 'public' AND owners.role = 'admin'))
              AND labs.vendor = %s
            ORDER BY is_completed ASC, labs.updated_at DESC
            """,
            (current_user.id, current_user.id, platform),
        )
    else:
        labs = fetch_all(
            """
            SELECT labs.*, topics.title AS topic_title,
                   owners.display_name AS owner_name, owners.role AS owner_role,
                   CASE WHEN completions.id IS NULL THEN 0 ELSE 1 END AS is_completed
            FROM lab_references AS labs
            JOIN users AS owners ON owners.id = labs.owner_id
            LEFT JOIN topics ON topics.id = labs.topic_id
            LEFT JOIN lab_completions AS completions
                   ON completions.lab_id = labs.id AND completions.user_id = %s
            WHERE labs.is_deleted = 0
              AND (labs.owner_id = %s OR (labs.visibility = 'public' AND owners.role = 'admin'))
            ORDER BY is_completed ASC, labs.updated_at DESC
            """,
            (current_user.id, current_user.id),
        )
    return render_template("labs/index.html", labs=labs, platforms=PLATFORMS, selected_platform=platform)


@labs_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        lab = read_lab_form()
        error = validate_lab(lab)
        if error:
            flash(error, "danger")
            return render_template("labs/form.html", lab=lab, topics=get_user_topics(), platforms=PLATFORMS)

        _, lab_id = execute(
            """
            INSERT INTO lab_references
                (name, vendor, url, notes, topic_id, owner_id, visibility, is_deleted, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0, NOW(), NOW())
            """,
            (
                lab["name"],
                lab["vendor"],
                lab["url"],
                lab["notes"],
                lab["topic_id"],
                current_user.id,
                lab["visibility"],
            ),
        )
        log_audit("lab_created", f"Created lab {lab['name']}")
        flash("Lab added successfully.", "success")
        return redirect(url_for("labs.detail", lab_id=lab_id))

    return render_template("labs/form.html", lab=None, topics=get_user_topics(), platforms=PLATFORMS)


@labs_bp.route("/<int:lab_id>")
@login_required
def detail(lab_id):
    lab = get_visible_lab_or_404(lab_id)
    return render_template("labs/detail.html", lab=lab)


@labs_bp.route("/<int:lab_id>/edit", methods=["GET", "POST"])
@login_required
def edit(lab_id):
    existing = get_owned_lab_or_404(lab_id)
    if request.method == "POST":
        lab = read_lab_form()
        lab["id"] = lab_id
        error = validate_lab(lab)
        if error:
            flash(error, "danger")
            return render_template("labs/form.html", lab=lab, topics=get_user_topics(), platforms=PLATFORMS)

        execute(
            """
            UPDATE lab_references
            SET name = %s, vendor = %s, url = %s, notes = %s,
                topic_id = %s, visibility = %s, updated_at = NOW()
            WHERE id = %s AND owner_id = %s AND is_deleted = 0
            """,
            (
                lab["name"],
                lab["vendor"],
                lab["url"],
                lab["notes"],
                lab["topic_id"],
                lab["visibility"],
                lab_id,
                current_user.id,
            ),
        )
        log_audit("lab_updated", f"Updated lab {lab['name']}")
        flash("Lab updated successfully.", "success")
        return redirect(url_for("labs.detail", lab_id=lab_id))

    return render_template("labs/form.html", lab=existing, topics=get_user_topics(), platforms=PLATFORMS)


@labs_bp.route("/<int:lab_id>/delete", methods=["POST"])
@login_required
def delete(lab_id):
    lab = get_owned_lab_or_404(lab_id)
    execute(
        "UPDATE lab_references SET is_deleted = 1, updated_at = NOW() WHERE id = %s AND owner_id = %s",
        (lab_id, current_user.id),
    )
    log_audit("lab_deleted", f"Deleted lab {lab['name']}")
    flash("Lab deleted successfully.", "info")
    return redirect(url_for("labs.index"))


@labs_bp.route("/<int:lab_id>/complete", methods=["POST"])
@login_required
def complete(lab_id):
    get_visible_lab_or_404(lab_id)
    execute(
        """
        INSERT INTO lab_completions (lab_id, user_id, completed_at)
        VALUES (%s, %s, NOW())
        ON DUPLICATE KEY UPDATE completed_at = VALUES(completed_at)
        """,
        (lab_id, current_user.id),
    )
    log_audit("lab_completed", f"Completed lab {lab_id}")
    flash("Lab marked complete.", "success")
    return redirect(url_for("labs.detail", lab_id=lab_id))


@labs_bp.route("/<int:lab_id>/incomplete", methods=["POST"])
@login_required
def incomplete(lab_id):
    get_visible_lab_or_404(lab_id)
    execute(
        "DELETE FROM lab_completions WHERE lab_id = %s AND user_id = %s",
        (lab_id, current_user.id),
    )
    flash("Lab marked incomplete.", "info")
    return redirect(url_for("labs.detail", lab_id=lab_id))


def get_visible_lab_or_404(lab_id):
    lab = fetch_one(
        """
        SELECT labs.*, topics.title AS topic_title,
               owners.display_name AS owner_name, owners.role AS owner_role,
               CASE WHEN completions.id IS NULL THEN 0 ELSE 1 END AS is_completed
        FROM lab_references AS labs
        JOIN users AS owners ON owners.id = labs.owner_id
        LEFT JOIN topics ON topics.id = labs.topic_id
        LEFT JOIN lab_completions AS completions
               ON completions.lab_id = labs.id AND completions.user_id = %s
        WHERE labs.id = %s AND labs.is_deleted = 0
          AND (labs.owner_id = %s OR (labs.visibility = 'public' AND owners.role = 'admin'))
        """,
        (current_user.id, lab_id, current_user.id),
    )
    if not lab:
        abort(404)
    return lab


def get_owned_lab_or_404(lab_id):
    lab = fetch_one(
        """
        SELECT *
        FROM lab_references
        WHERE id = %s AND owner_id = %s AND is_deleted = 0
        """,
        (lab_id, current_user.id),
    )
    if not lab:
        abort(404)
    return lab


def get_user_topics():
    return fetch_all(
        "SELECT id, title FROM topics WHERE owner_id = %s AND is_deleted = 0 ORDER BY title",
        (current_user.id,),
    )


def read_lab_form():
    visibility = clean_text(request.form.get("visibility"))
    if not current_user.is_admin or visibility not in {"personal", "public"}:
        visibility = "personal"
    return {
        "name": clean_text(request.form.get("name")),
        "vendor": clean_text(request.form.get("vendor")),
        "url": clean_text(request.form.get("url")),
        "notes": clean_text(request.form.get("notes")),
        "topic_id": request.form.get("topic_id", type=int) or None,
        "visibility": visibility,
    }


def validate_lab(lab):
    if not lab["name"]:
        return "Lab name is required."
    if lab["vendor"] not in PLATFORMS:
        return "Choose a valid lab platform."
    parsed_url = urlparse(lab["url"])
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return "Enter a valid HTTP or HTTPS lab URL."
    if lab["topic_id"] and not fetch_one(
        "SELECT id FROM topics WHERE id = %s AND owner_id = %s AND is_deleted = 0",
        (lab["topic_id"], current_user.id),
    ):
        return "Choose one of your own topics."
    return None
