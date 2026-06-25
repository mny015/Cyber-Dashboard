from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from utils.decorators import admin_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    return render_template("index.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    # Redirect to role-specific dashboard
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("dashboard.admin_dashboard"))
    return redirect(url_for("dashboard.user_dashboard"))


@dashboard_bp.route("/user/dashboard")
@login_required
def user_dashboard():
    if getattr(current_user, "is_admin", False):
        # Admins should use the admin dashboard
        return redirect(url_for("dashboard.admin_dashboard"))
    return render_template("user/dashboard.html")


@dashboard_bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")