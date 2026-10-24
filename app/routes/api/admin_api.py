from flask import Blueprint, jsonify, request, session

from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.utils.api_auth import api_roles_required

admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/api")


@admin_api_bp.route("/admin/users", methods=["GET"])
@api_roles_required("admin")
def users():
    records = UserRepository().list_users()
    return jsonify({"users": [
        {key: value for key, value in item.items() if key != "password_hash"}
        for item in records
    ]})


@admin_api_bp.route("/admin/users/<user_id>", methods=["PATCH"])
@api_roles_required("admin")
def update_user(user_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    role = payload.get("role")
    if role is not None and role not in {"candidate", "recruiter", "admin"}:
        return jsonify({"status": "error", "message": "Choose a valid role."}), 400
    if "active" in payload and not isinstance(payload["active"], bool):
        return jsonify({"status": "error", "message": "The active value must be a boolean."}), 400
    if user_id == session["user"]["id"] and payload.get("active") is False:
        return jsonify({"status": "error", "message": "You cannot deactivate your own account."}), 400
    updates = {key: payload[key] for key in ("role", "active") if key in payload}
    user = UserRepository().update_one(user_id, updates)
    if not user:
        return jsonify({"status": "error", "message": "User not found."}), 404
    AuditService().record(session["user"]["id"], "user.updated", "user", user_id, updates)
    return jsonify({"user": {key: value for key, value in user.items() if key != "password_hash"}})


@admin_api_bp.route("/admin/audit-logs", methods=["GET"])
@api_roles_required("admin")
def audit_logs():
    return jsonify({"logs": AuditService().recent()})
