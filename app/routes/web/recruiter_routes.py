import uuid
import os

from flask import Blueprint, abort, flash, redirect, render_template, request, send_from_directory, session, url_for

from app.routes.web.auth_routes import login_required, role_required
from app.repositories.resume_repository import ResumeRepository
from app.services.analytics_service import AnalyticsService
from app.services.job_service import JobService
from app.services.application_service import ApplicationService
from app.services.audit_service import AuditService
from app.services.interview_service import InterviewService
from app.services.notification_service import NotificationService

recruiter_bp = Blueprint("recruiter", __name__, template_folder="../../templates")
job_service = JobService()
analytics = AnalyticsService()
application_service = ApplicationService()
interview_service = InterviewService()
notification_service = NotificationService()
audit_service = AuditService()


@recruiter_bp.route("/recruiter/dashboard")
@login_required
@role_required("recruiter")
def dashboard():
    jobs = job_service.repo.by_recruiter(session["user"]["id"])
    metrics = analytics.dashboard_metrics()
    applications = [
        application
        for job in jobs
        for application in application_service.job_applications(job["id"])
    ]
    metrics["total_applications"] = len(applications)
    metrics["candidate_count"] = len({item["candidate_id"] for item in applications})
    return render_template("recruiter/dashboard.html", jobs=jobs, metrics=metrics, user=session.get("user"))


@recruiter_bp.route("/recruiter/jobs", methods=["GET", "POST"])
@login_required
@role_required("recruiter")
def jobs():
    if request.method == "POST":
        payload = {
            "id": uuid.uuid4().hex,
            "title": request.form.get("title"),
            "company": request.form.get("company", "HireHub"),
            "location": request.form.get("location", "Remote"),
            "job_type": request.form.get("job_type", "full-time"),
            "salary": request.form.get("salary", "Competitive"),
            "category": request.form.get("category", "Engineering"),
            "description": request.form.get("description", ""),
            "requirements": [item.strip() for item in (request.form.get("requirements") or "").split(",") if item.strip()],
            "posted_by": session["user"]["id"],
        }
        try:
            job = job_service.create_job(payload)
            audit_service.record(session["user"]["id"], "job.created", "job", job["id"])
            flash("Job published successfully.", "success")
            return redirect(url_for("recruiter.jobs"))
        except ValueError as exc:
            flash(str(exc), "danger")
    jobs = job_service.repo.by_recruiter(session["user"]["id"])
    return render_template("recruiter/jobs.html", jobs=jobs, user=session.get("user"))


@recruiter_bp.route("/recruiter/jobs/<job_id>/delete", methods=["POST"])
@login_required
@role_required("recruiter")
def delete_job(job_id):
    try:
        job = job_service.delete_job(job_id, session["user"]["id"])
        audit_service.record(session["user"]["id"], "job.deleted", "job", job["id"])
        flash("Job deleted.", "success")
    except (ValueError, PermissionError) as exc:
        flash(str(exc), "danger")
    return redirect(url_for("recruiter.jobs"))


@recruiter_bp.route("/recruiter/jobs/<job_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("recruiter")
def edit_job(job_id):
    job = job_service.get_job(job_id)
    if not job or job.get("posted_by") != session["user"]["id"]:
        flash("Job not found or access denied.", "danger")
        return redirect(url_for("recruiter.jobs"))
    if request.method == "POST":
        payload = {
            "title": request.form.get("title", "").strip(),
            "company": request.form.get("company", "").strip(),
            "location": request.form.get("location", "").strip(),
            "job_type": request.form.get("job_type", "").strip(),
            "salary": request.form.get("salary", "").strip(),
            "category": request.form.get("category", "").strip(),
            "description": request.form.get("description", "").strip(),
            "requirements": [item.strip() for item in request.form.get("requirements", "").split(",") if item.strip()],
        }
        try:
            job = job_service.update_job(job_id, session["user"]["id"], payload)
            audit_service.record(session["user"]["id"], "job.updated", "job", job_id)
            flash("Job updated.", "success")
            return redirect(url_for("recruiter.jobs"))
        except (ValueError, PermissionError) as exc:
            flash(str(exc), "danger")
    return render_template("recruiter/edit_job.html", job=job, user=session.get("user"))


@recruiter_bp.route("/recruiter/applications", methods=["GET", "POST"])
@login_required
@role_required("recruiter")
def applications():
    recruiter_id = session["user"]["id"]
    jobs = job_service.repo.by_recruiter(recruiter_id)
    applications = [
        application
        for job in jobs
        for application in application_service.job_applications(job["id"])
    ]
    users = {user["id"]: user for user in analytics.user_repo.list_users()}
    if request.method == "POST":
        try:
            updated = application_service.update_status(
                request.form.get("application_id", ""),
                recruiter_id,
                request.form.get("status", ""),
            )
            candidate = users.get(updated["candidate_id"], {})
            flash(f"Application updated for {candidate.get('email', 'candidate')}.", "success")
            return redirect(url_for("recruiter.applications"))
        except (ValueError, PermissionError) as exc:
            flash(str(exc), "danger")
    return render_template(
        "recruiter/applications.html",
        applications=applications,
        users=users,
        jobs={job["id"]: job for job in jobs},
        resumes={
            candidate_id: ResumeRepository().for_candidate(candidate_id)
            for candidate_id in {item["candidate_id"] for item in applications}
        },
        user=session.get("user"),
    )


@recruiter_bp.route("/recruiter/interviews", methods=["GET", "POST"])
@login_required
@role_required("recruiter")
def interviews():
    recruiter_id = session["user"]["id"]
    if request.method == "POST":
        try:
            interview = interview_service.schedule(request.form, recruiter_id)
            audit_service.record(recruiter_id, "interview.scheduled", "interview", interview["id"])
            flash("Interview scheduled and candidate notified.", "success")
            return redirect(url_for("recruiter.interviews"))
        except (ValueError, PermissionError) as exc:
            flash(str(exc), "danger")
    applications = [
        application
        for job in job_service.repo.by_recruiter(recruiter_id)
        for application in application_service.job_applications(job["id"])
    ]
    return render_template(
        "recruiter/interviews.html",
        interviews=interview_service.for_recruiter(recruiter_id),
        applications=applications,
        user=session.get("user"),
    )


@recruiter_bp.route("/recruiter/notifications")
@login_required
@role_required("recruiter")
def notifications():
    items = notification_service.for_user(session["user"]["id"])
    return render_template("shared/notifications.html", notifications=items, user=session.get("user"))


@recruiter_bp.route("/recruiter/resumes/<resume_id>/download")
@login_required
@role_required("recruiter")
def download_candidate_resume(resume_id):
    resume = ResumeRepository().find_by_id(resume_id)
    if not resume:
        abort(404)
    recruiter_job_ids = {job["id"] for job in job_service.repo.by_recruiter(session["user"]["id"])}
    applied = any(
        application.get("candidate_id") == resume["candidate_id"]
        for job_id in recruiter_job_ids
        for application in application_service.job_applications(job_id)
    )
    if not applied:
        abort(404)
    return send_from_directory(
        os.path.dirname(resume["storage_path"]),
        os.path.basename(resume["storage_path"]),
        as_attachment=True,
        download_name=resume.get("original_name", "resume"),
    )
