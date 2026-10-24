from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService

auth_bp = Blueprint("auth", __name__, template_folder="../../templates")
auth_service = AuthService()
audit_service = AuditService()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = UserRepository().get_by_id(user_id)
    if not user or not user.get("active", True):
        return None
    safe_user = {key: value for key, value in user.items() if key != "password_hash"}
    session["user"] = safe_user
    return safe_user


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            session.clear()
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                session.clear()
                flash("Please log in first.", "warning")
                return redirect(url_for("auth.login"))
            if user.get("role") not in roles:
                flash("You are not authorized for this resource.", "danger")
                return redirect(url_for("dashboard.index"))
            return func(*args, **kwargs)
        return wrapper
    return decorator


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        try:
            user = auth_service.login(email, password)
            session_user = {key: value for key, value in user.items() if key != "password_hash"}
            session.clear()
            session["user_id"] = session_user["id"]
            session["user"] = session_user
            session.permanent = True
            audit_service.record(user["id"], "auth.login", "user", user["id"])
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        payload = {
            "first_name": request.form.get("first_name", ""),
            "last_name": request.form.get("last_name", ""),
            "email": request.form.get("email", ""),
            "password": request.form.get("password", ""),
            "role": request.form.get("role", "candidate"),
        }
        try:
            auth_service.register(payload)
            audit_service.record(payload["email"].strip().lower(), "auth.register", "user", payload["email"].strip().lower())
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    user = session.get("user")
    if user:
        audit_service.record(user.get("id"), "auth.logout", "user", user.get("id", ""))
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
