import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory, session

from app.services.audit_service import AuditService
from app.services.resume_service import ResumeService
from app.utils.api_auth import api_roles_required
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository

resume_api_bp = Blueprint("resume_api", __name__, url_prefix="/api")


def resume_service():
    return ResumeService(current_app.config["UPLOAD_FOLDER"])


@resume_api_bp.route("/resumes", methods=["GET", "POST"])
@api_roles_required("candidate")
def resumes():
    service = resume_service()
    candidate_id = session["user"]["id"]
    if request.method == "GET":
        return jsonify({"resumes": [
            {key: value for key, value in item.items() if key != "storage_path"}
            for item in service.list_for_candidate(candidate_id)
        ]})
    file = request.files.get("resume")
    try:
        saved = service.save_resume(file, candidate_id)
        AuditService().record(candidate_id, "resume.uploaded", "resume", saved["id"])
        return jsonify({"resume": {key: value for key, value in saved.items() if key != "storage_path"}}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@resume_api_bp.route("/resumes/<resume_id>/download")
@api_roles_required("candidate", "recruiter", "admin")
def download_resume(resume_id):
    resume = resume_service().find_resume(resume_id)
    user = session["user"]
    if not resume:
        return jsonify({"status": "error", "message": "Resume not found."}), 404
    if user["role"] == "candidate" and resume["candidate_id"] != user["id"]:
        return jsonify({"status": "error", "message": "Resume not found."}), 404
    if user["role"] == "recruiter":
        recruiter_jobs = {job["id"] for job in JobRepository().by_recruiter(user["id"])}
        has_application = any(
            application.get("candidate_id") == resume["candidate_id"]
            for job_id in recruiter_jobs
            for application in ApplicationRepository().by_job(job_id)
        )
        if not has_application:
            return jsonify({"status": "error", "message": "Resume not found."}), 404
    return send_from_directory(
        os.path.dirname(resume["storage_path"]),
        os.path.basename(resume["storage_path"]),
        as_attachment=True,
        download_name=resume.get("original_name", "resume"),
    )
