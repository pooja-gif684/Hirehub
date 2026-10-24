from flask import Blueprint, jsonify, request, session

from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.services.company_service import CompanyService
from app.services.application_service import ApplicationService
from app.services.interview_service import InterviewService
from app.services.job_service import JobService
from app.services.notification_service import NotificationService
from app.services.audit_service import AuditService
from app.utils.api_auth import api_roles_required

recruiter_api_bp = Blueprint("recruiter_api", __name__, url_prefix="/api")
company_service = CompanyService()
user_repository = UserRepository()


@recruiter_api_bp.route("/recruiter/company", methods=["GET", "PATCH"])
@api_roles_required("recruiter")
def company_profile():
    recruiter_id = session["user"]["id"]
    if request.method == "GET":
        company = company_service.get_for_recruiter(recruiter_id)
        return jsonify({"company": company})

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    try:
        company = company_service.update_for_recruiter(recruiter_id, payload)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    user = user_repository.get_by_id(recruiter_id)
    session["user"] = {key: value for key, value in user.items() if key != "password_hash"}
    AuditService().record(recruiter_id, "company.profile_updated", "company", company["id"] if company else "")
    return jsonify({"company": company})


@recruiter_api_bp.route("/recruiter/jobs")
@api_roles_required("recruiter")
def jobs():
    return jsonify({"jobs": JobRepository().by_recruiter(session["user"]["id"])})


@recruiter_api_bp.route("/recruiter/applications")
@api_roles_required("recruiter")
def applications():
    job_repo = JobRepository()
    application_service = ApplicationService()
    items = [
        application
        for job in job_repo.by_recruiter(session["user"]["id"])
        for application in application_service.job_applications(job["id"])
    ]
    return jsonify({"applications": items})


@recruiter_api_bp.route("/recruiter/interviews")
@api_roles_required("recruiter")
def interviews():
    return jsonify({"interviews": InterviewService().for_recruiter(session["user"]["id"])})


@recruiter_api_bp.route("/recruiter/notifications")
@api_roles_required("recruiter")
def notifications():
    return jsonify({"notifications": NotificationService().for_user(session["user"]["id"])})


@recruiter_api_bp.route("/recruiter/jobs/<job_id>", methods=["PATCH", "DELETE"])
@api_roles_required("recruiter")
def manage_job(job_id):
    service = JobService()
    if request.method == "DELETE":
        try:
            job = service.delete_job(job_id, session["user"]["id"])
            AuditService().record(session["user"]["id"], "job.deleted", "job", job_id)
            return jsonify({"job": job})
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 404
        except PermissionError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 403
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    try:
        job = service.update_job(job_id, session["user"]["id"], payload)
        AuditService().record(session["user"]["id"], "job.updated", "job", job_id)
        return jsonify({"job": job})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 403
