from flask import Blueprint, jsonify, request, session

from app.repositories.job_repository import JobRepository
from app.services.audit_service import AuditService
from app.services.job_service import JobService
from app.utils.api_auth import api_roles_required

job_api_bp = Blueprint("job_api", __name__, url_prefix="/api")
job_service = JobService()
job_repository = JobRepository()
audit_service = AuditService()


@job_api_bp.route("/jobs", methods=["GET"]) 
def list_jobs():
    filters = {
        "query": request.args.get("query"),
        "location": request.args.get("location"),
        "category": request.args.get("category"),
        "job_type": request.args.get("job_type"),
    }
    return jsonify({"jobs": job_service.list_jobs(filters)})


@job_api_bp.route("/jobs", methods=["POST"])
@api_roles_required("recruiter", "admin")
def create_job():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    payload["posted_by"] = session["user"]["id"]
    try:
        job = job_service.create_job(payload)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    audit_service.record(session["user"]["id"], "job.created", "job", job["id"])
    return jsonify({"status": "success", "job": job}), 201


@job_api_bp.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    job = job_service.get_job(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found."}), 404
    return jsonify({"job": job})


@job_api_bp.route("/jobs/<job_id>", methods=["PATCH"])
@api_roles_required("recruiter", "admin")
def update_job(job_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    try:
        job = job_repository.find_by_id(job_id)
        if not job:
            return jsonify({"status": "error", "message": "Job not found."}), 404
        if session["user"]["role"] != "admin" and job.get("posted_by") != session["user"]["id"]:
            return jsonify({"status": "error", "message": "You cannot edit this job."}), 403
        updates = {key: value for key, value in payload.items() if key in {
            "title", "company", "location", "job_type", "salary",
            "category", "description", "requirements", "status",
        }}
        updated = job_service.update_job(job_id, job.get("posted_by"), updates)
        audit_service.record(session["user"]["id"], "job.updated", "job", job_id)
        return jsonify({"job": updated})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@job_api_bp.route("/jobs/<job_id>", methods=["DELETE"])
@api_roles_required("recruiter", "admin")
def delete_job(job_id):
    job = job_repository.find_by_id(job_id)
    if not job:
        return jsonify({"status": "error", "message": "Job not found."}), 404
    if session["user"]["role"] != "admin" and job.get("posted_by") != session["user"]["id"]:
        return jsonify({"status": "error", "message": "You cannot delete this job."}), 403
    job_repository.delete_one(job_id)
    audit_service.record(session["user"]["id"], "job.deleted", "job", job_id)
    return jsonify({"status": "success"})
