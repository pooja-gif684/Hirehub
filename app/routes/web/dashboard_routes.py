from flask import Blueprint, redirect, url_for
from app.routes.web.auth_routes import current_user, login_required

dashboard_bp = Blueprint("dashboard", __name__, template_folder="../../templates")


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user = current_user() or {}
    role = user.get("role")
    if role == "recruiter":
        return redirect(url_for("recruiter.dashboard"))
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    if role == "candidate":
        return redirect(url_for("candidate.dashboard"))
    session.clear()
    return redirect(url_for("auth.login"))
