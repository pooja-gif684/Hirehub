import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.routes.web.auth_routes import login_required, role_required
from app.repositories.user_repository import UserRepository
from app.services.application_service import ApplicationService
from app.services.candidate_service import CandidateService
from app.services.company_service import CompanyService
from app.services.job_service import JobService
from app.services.recommendation_service import RecommendationService
from app.services.resume_service import ResumeService
from app.services.interview_service import InterviewService
from app.services.notification_service import NotificationService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

candidate_bp = Blueprint("candidate", __name__, template_folder="../../templates")
job_service = JobService()
application_service = ApplicationService()
recommendation_service = RecommendationService(job_service)
interview_service = InterviewService()
notification_service = NotificationService()
audit_service = AuditService()
auth_service = AuthService()
candidate_service = CandidateService()
company_service = CompanyService()


def get_resume_service():
    return ResumeService(current_app.config["UPLOAD_FOLDER"])


@candidate_bp.route("/candidate/dashboard")
@login_required
@role_required("candidate")
def dashboard():
    user = session.get("user")
    jobs = job_service.list_jobs()[:3]
    applications = application_service.candidate_applications(user["id"])
    interviews = interview_service.for_candidate(user["id"])
    recommendations = recommendation_service.recommend_for_candidate(user)[:3]
    notifications = notification_service.for_user(user["id"])
    return render_template(
        "candidate/dashboard.html",
        user=user,
        jobs=recommendations or jobs,
        application_count=len(applications),
        interview_count=len(interviews),
        unread_count=sum(not item.get("is_read", False) for item in notifications),
    )


@candidate_bp.route("/candidate/jobs")
@login_required
@role_required("candidate")
def jobs():
    jobs = job_service.list_jobs({
        "query": request.args.get("query"),
        "location": request.args.get("location"),
        "category": request.args.get("category"),
        "job_type": request.args.get("job_type")
    })
    return render_template("jobs/list.html", jobs=jobs, user=session.get("user"))


@candidate_bp.route("/candidate/applications")
@login_required
@role_required("candidate")
def applications():
    apps = application_service.candidate_applications(session["user"]["id"])
    jobs = {job["id"]: job for job in job_service.list_jobs()}
    for application in apps:
        application["job_title"] = jobs.get(application["job_id"], {}).get("title", "Job no longer available")
    return render_template("candidate/applications.html", applications=apps, user=session.get("user"))


@candidate_bp.route("/candidate/interviews")
@login_required
@role_required("candidate")
def interviews():
    items = interview_service.for_candidate(session["user"]["id"])
    return render_template("candidate/interviews.html", interviews=items, user=session.get("user"))


@candidate_bp.route("/candidate/notifications", methods=["GET", "POST"])
@login_required
@role_required("candidate")
def notifications():
    user_id = session["user"]["id"]
    if request.method == "POST":
        notification_id = request.form.get("notification_id")
        try:
            if notification_id:
                notification_service.mark_read(notification_id, user_id)
            else:
                notification_service.mark_all_read(user_id)
            flash("Notifications updated.", "success")
        except (ValueError, PermissionError) as exc:
            flash(str(exc), "danger")
        return redirect(url_for("candidate.notifications"))
    return render_template(
        "candidate/notifications.html",
        notifications=notification_service.for_user(user_id),
        user=session.get("user"),
    )


@candidate_bp.route("/candidate/recommendations")
@login_required
@role_required("candidate")
def recommendations():
    candidate = session.get("user", {})
    suggestions = recommendation_service.recommend_for_candidate(candidate)
    return render_template("candidate/recommendations.html", recommendations=suggestions, user=session.get("user"))


@candidate_bp.route("/candidate/resume", methods=["GET", "POST"])
@login_required
@role_required("candidate")
def resume():
    service = get_resume_service()
    if request.method == "POST":
        file = request.files.get("resume")
        try:
            result = service.save_resume(file, session["user"]["id"])
            audit_service.record(session["user"]["id"], "resume.uploaded", "resume", result["id"])
            flash(f"Resume uploaded: {result['filename']}", "success")
        except ValueError as exc:
            flash(str(exc), "danger")
    resumes = service.list_for_candidate(session["user"]["id"])
    return render_template("candidate/resume.html", user=session.get("user"), resumes=resumes)


@candidate_bp.route("/candidate/resume/<resume_id>/download")
@login_required
@role_required("candidate")
def download_resume(resume_id):
    from flask import abort, send_from_directory

    resume = get_resume_service().find_resume(resume_id)
    if not resume or resume.get("candidate_id") != session["user"]["id"]:
        abort(404)
    return send_from_directory(
        os.path.dirname(resume["storage_path"]),
        os.path.basename(resume["storage_path"]),
        as_attachment=True,
        download_name=resume.get("original_name", "resume"),
    )


@candidate_bp.route("/candidate/profile", methods=["GET", "POST"])
@login_required
@role_required("candidate")
def profile():
    return account_profile()


@candidate_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("candidate", "recruiter", "admin")
def account_profile():
    user = session["user"]
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        if current_password or new_password:
            try:
                auth_service.change_password(user["id"], current_password, new_password)
                audit_service.record(user["id"], "auth.password_changed", "user", user["id"])
                flash("Password updated.", "success")
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("candidate/profile.html", user=user), 400
        profile_fields = {
            "first_name", "last_name", "headline", "location", "skills", "company", "position",
        }
        if profile_fields.intersection(request.form):
            updates = {
                "first_name": request.form.get("first_name", "").strip(),
                "last_name": request.form.get("last_name", "").strip(),
                "headline": request.form.get("headline", "").strip(),
                "location": request.form.get("location", "").strip(),
                "skills": [skill.strip() for skill in request.form.get("skills", "").split(",") if skill.strip()],
                "company": request.form.get("company", "").strip(),
                "position": request.form.get("position", "").strip(),
            }
            if user.get("role") == "candidate":
                updated_user = candidate_service.update_profile(user["id"], updates)
            else:
                updated_user = UserRepository().update_one(user["id"], updates)
            if not updated_user:
                flash("Unable to find your account. Please log in again.", "danger")
                return render_template("candidate/profile.html", user=user), 404
            if user.get("role") == "recruiter":
                company_service.update_for_recruiter(user["id"], {
                    "name": updates["company"],
                    "position": updates["position"],
                    "location": updates["location"],
                })
            session["user"] = {key: value for key, value in updated_user.items() if key != "password_hash"}
            audit_service.record(user["id"], "profile.updated", "user", user["id"])
            flash("Profile updated successfully.", "success")
        return render_template("candidate/profile.html", user=session.get("user", user))
    return render_template("candidate/profile.html", user=user)
