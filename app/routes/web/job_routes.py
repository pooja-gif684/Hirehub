from flask import Blueprint, render_template, request, session
from app.services.job_service import JobService

job_bp = Blueprint("jobs", __name__, template_folder="../../templates")
job_service = JobService()


@job_bp.route("/jobs")
def list_jobs():
    jobs = job_service.list_jobs({
        "query": request.args.get("query"),
        "location": request.args.get("location"),
        "category": request.args.get("category"),
        "job_type": request.args.get("job_type")
    })
    return render_template("jobs/list.html", jobs=jobs, user=session.get("user"), filters=request.args)


@job_bp.route("/jobs/<job_id>")
def detail(job_id):
    job = job_service.get_job(job_id)
    if job is None:
        return "Job not found", 404
    return render_template("jobs/detail.html", job=job, user=session.get("user"))
