from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.routes.web.auth_routes import login_required, role_required
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.report_service import ReportService
from app.repositories.user_repository import UserRepository
from app.repositories.job_repository import JobRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.interview_repository import InterviewRepository
from app.services.notification_service import NotificationService

admin_bp = Blueprint("admin", __name__, template_folder="../../templates")
analytics_service = AnalyticsService()
audit_service = AuditService()
report_service = ReportService()
user_repository = UserRepository()
job_repository = JobRepository()
application_repository = ApplicationRepository()
notification_service = NotificationService()
interview_repository = InterviewRepository()


@admin_bp.route("/admin/dashboard")
@login_required
@role_required("admin")
def dashboard():
    metrics = analytics_service.dashboard_metrics()
    return render_template("admin/dashboard.html", metrics=metrics, user=session.get("user"))


@admin_bp.route("/admin/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def users():
    if request.method == "POST":
        user_id = request.form.get("user_id", "")
        role = request.form.get("role", "")
        active = request.form.get("active") == "true"
        if role not in {"candidate", "recruiter", "admin"}:
            flash("Select a valid role.", "danger")
        elif user_id == session["user"]["id"] and not active:
            flash("You cannot deactivate your own account.", "danger")
        else:
            updated = user_repository.update_one(user_id, {"role": role, "active": active})
            if updated:
                audit_service.record(session["user"]["id"], "user.updated", "user", user_id, {"role": role, "active": active})
                flash("User updated.", "success")
            else:
                flash("User not found.", "danger")
        return redirect(url_for("admin.users"))
    users = [
        {key: value for key, value in user.items() if key != "password_hash"}
        for user in user_repository.list_users()
    ]
    return render_template("admin/users.html", user=session.get("user"), users=users)


@admin_bp.route("/admin/reports")
@login_required
@role_required("admin")
def reports():
    return render_template(
        "admin/reports.html",
        user=session.get("user"),
        report=report_service.generate(),
    )


@admin_bp.route("/admin/audit-logs")
@login_required
@role_required("admin")
def audit_logs():
    return render_template(
        "admin/audit_logs.html",
        user=session.get("user"),
        logs=audit_service.recent(),
    )


@admin_bp.route("/admin/jobs", methods=["GET", "POST"])
@login_required
@role_required("admin")
def jobs():
    if request.method == "POST":
        job_id = request.form.get("job_id", "")
        action = request.form.get("action", "")
        if action == "delete":
            job = job_repository.delete_one(job_id)
            if job:
                audit_service.record(session["user"]["id"], "job.deleted", "job", job_id)
                flash("Job deleted.", "success")
            else:
                flash("Job not found.", "danger")
        elif action == "toggle":
            job = job_repository.find_by_id(job_id)
            if job:
                status = "closed" if job.get("status", "open") == "open" else "open"
                job_repository.update_one(job_id, {"status": status})
                audit_service.record(session["user"]["id"], "job.status_updated", "job", job_id, {"status": status})
                flash(f"Job {status}.", "success")
            else:
                flash("Job not found.", "danger")
        return redirect(url_for("admin.jobs"))
    return render_template(
        "admin/jobs.html",
        user=session.get("user"),
        jobs=job_repository.list_jobs(),
    )


@admin_bp.route("/admin/applications", methods=["GET", "POST"])
@login_required
@role_required("admin")
def applications():
    if request.method == "POST":
        application_id = request.form.get("application_id", "")
        status = request.form.get("status", "")
        if status not in {"applied", "reviewing", "shortlisted", "rejected", "hired"}:
            flash("Choose a valid application status.", "danger")
        else:
            application = application_repository.update_status(application_id, status)
            if application:
                notification_service.create(
                    application["candidate_id"],
                    f"Your application status was updated to {status}.",
                    "application",
                )
                audit_service.record(session["user"]["id"], "application.status_updated", "application", application_id, {"status": status})
                flash("Application status updated.", "success")
            else:
                flash("Application not found.", "danger")
        return redirect(url_for("admin.applications"))
    applications = application_repository.find_all()
    jobs = {job["id"]: job for job in job_repository.list_jobs()}
    return render_template(
        "admin/applications.html",
        user=session.get("user"),
        applications=applications,
        jobs=jobs,
    )


@admin_bp.route("/admin/interviews")
@login_required
@role_required("admin")
def interviews():
    return render_template(
        "admin/interviews.html",
        user=session.get("user"),
        interviews=interview_repository.find_all(),
    )
