from flask import Blueprint, jsonify, request, session

from app.services.application_service import ApplicationService
from app.repositories.job_repository import JobRepository
from app.utils.api_auth import api_roles_required

application_api_bp = Blueprint("application_api", __name__, url_prefix="/api")
application_service = ApplicationService()


@application_api_bp.route("/applications", methods=["POST"]) 
@api_roles_required("candidate")
def apply():
    user = session["user"]
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    try:
        application = application_service.apply_for_job(
            job_id=payload.get("job_id"),
            candidate_id=user["id"],
            cover_letter=payload.get("cover_letter", ""),
        )
        return jsonify({"status": "success", "application": application}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@application_api_bp.route("/applications/me", methods=["GET"])
@api_roles_required("candidate")
def list_for_candidate():
    return jsonify({"applications": application_service.candidate_applications(session["user"]["id"])})


@application_api_bp.route("/applications/<job_id>", methods=["GET"])
@api_roles_required("recruiter", "admin")
def list_for_job(job_id):
    job = JobRepository().find_by_id(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found."}), 404
    if session["user"]["role"] != "admin" and job.get("posted_by") != session["user"]["id"]:
        return jsonify({"status": "error", "message": "You cannot view these applications."}), 403
    return jsonify({"applications": application_service.job_applications(job_id)})


@application_api_bp.route("/applications/<application_id>/status", methods=["PATCH"])
@api_roles_required("recruiter")
def update_status(application_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    try:
        application = application_service.update_status(
            application_id,
            session["user"]["id"],
            payload.get("status"),
        )
        return jsonify({"application": application})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 403
