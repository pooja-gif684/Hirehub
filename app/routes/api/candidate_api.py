from flask import Blueprint, jsonify, request, session

from app.services.application_service import ApplicationService
from app.services.candidate_service import CandidateService
from app.services.interview_service import InterviewService
from app.services.notification_service import NotificationService
from app.services.recommendation_service import RecommendationService
from app.services.job_service import JobService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.utils.api_auth import api_roles_required

candidate_api_bp = Blueprint("candidate_api", __name__, url_prefix="/api")
candidate_service = CandidateService()


@candidate_api_bp.route("/candidate/profile", methods=["GET", "PATCH"])
@api_roles_required("candidate")
def profile():
    user = candidate_service.get_profile(session["user"]["id"])
    if not user:
        return jsonify({"status": "error", "message": "User not found."}), 404
    if request.method == "PATCH":
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
        if "current_password" in payload or "new_password" in payload:
            try:
                AuthService().change_password(
                    user["id"],
                    payload.get("current_password", ""),
                    payload.get("new_password", ""),
                )
                AuditService().record(user["id"], "auth.password_changed", "user", user["id"])
            except ValueError as exc:
                return jsonify({"status": "error", "message": str(exc)}), 400
        updates = {key: payload[key] for key in candidate_service.PROFILE_FIELDS if key in payload}
        try:
            user = candidate_service.update_profile(user["id"], updates)
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
        session["user"] = {key: value for key, value in user.items() if key != "password_hash"}
        AuditService().record(user["id"], "profile.updated", "user", user["id"])
    return jsonify({"profile": {key: value for key, value in user.items() if key != "password_hash"}})


@candidate_api_bp.route("/candidate/recommendations")
@api_roles_required("candidate")
def recommendations():
    recommender = RecommendationService(JobService())
    return jsonify({"recommendations": recommender.recommend_for_candidate(session["user"])})


@candidate_api_bp.route("/candidate/interviews")
@api_roles_required("candidate")
def interviews():
    return jsonify({"interviews": InterviewService().for_candidate(session["user"]["id"])})


@candidate_api_bp.route("/candidate/notifications", methods=["GET", "PATCH"])
@api_roles_required("candidate")
def notifications():
    service = NotificationService()
    user_id = session["user"]["id"]
    if request.method == "GET":
        return jsonify({"notifications": service.for_user(user_id)})
    payload = request.get_json(silent=True) or {}
    try:
        if payload.get("all"):
            service.mark_all_read(user_id)
            return jsonify({"status": "success"})
        notification = service.mark_read(payload.get("notification_id"), user_id)
        return jsonify({"notification": notification})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 403


@candidate_api_bp.route("/notifications", methods=["GET", "PATCH"])
@api_roles_required("candidate", "recruiter", "admin")
def user_notifications():
    service = NotificationService()
    user_id = session["user"]["id"]
    if request.method == "GET":
        return jsonify({"notifications": service.for_user(user_id)})
    payload = request.get_json(silent=True) or {}
    try:
        if payload.get("all"):
            service.mark_all_read(user_id)
            return jsonify({"status": "success"})
        notification = service.mark_read(payload.get("notification_id"), user_id)
        return jsonify({"notification": notification})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 403


@candidate_api_bp.route("/candidate/applications")
@api_roles_required("candidate")
def applications():
    items = ApplicationService().candidate_applications(session["user"]["id"])
    return jsonify({"applications": items})
