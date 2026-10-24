from flask import Blueprint, jsonify, request, session
from app.services.audit_service import AuditService

from app.services.auth_service import AuthService

auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/api")
auth_service = AuthService()
audit_service = AuditService()


def public_user(user):
    return {key: value for key, value in user.items() if key != "password_hash"}


@auth_api_bp.route("/auth/register", methods=["POST"]) 
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    try:
        user = auth_service.register(payload)
        audit_service.record(user["id"], "auth.register", "user", user["id"])
        return jsonify({"status": "success", "user": public_user(user)}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@auth_api_bp.route("/auth/login", methods=["POST"]) 
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    try:
        user = auth_service.login(payload.get("email", ""), payload.get("password", ""))
        safe_user = public_user(user)
        session.clear()
        session["user_id"] = safe_user["id"]
        session["user"] = safe_user
        session.permanent = True
        audit_service.record(user["id"], "auth.login", "user", user["id"])
        return jsonify({"status": "success", "user": safe_user}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 401


@auth_api_bp.route("/auth/logout", methods=["POST"])
def logout():
    user = session.get("user")
    if user:
        audit_service.record(user.get("id"), "auth.logout", "user", user.get("id", ""))
    session.clear()
    return jsonify({"status": "success", "message": "Logged out."})
