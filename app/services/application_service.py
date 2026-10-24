from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from pymongo.errors import DuplicateKeyError
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class ApplicationService:
    def __init__(self, repo=None, job_repo=None, notifications=None, audit=None):
        self.repo = repo or ApplicationRepository()
        self.job_repo = job_repo or JobRepository()
        self.notifications = notifications or NotificationService()
        self.audit = audit or AuditService()

    def apply_for_job(self, job_id, candidate_id, cover_letter=""):
        if not isinstance(job_id, str) or not job_id:
            raise ValueError("A job is required to submit an application.")
        if not isinstance(cover_letter, str) or len(cover_letter) > 10000:
            raise ValueError("Cover letter must be text of at most 10,000 characters.")
        job = self.job_repo.find_by_id(job_id)
        if not job or job.get("status", "open") != "open":
            raise ValueError("This job is no longer available.")
        if self.repo.find_one(job_id=job_id, candidate_id=candidate_id):
            raise ValueError("You have already applied for this job.")
        try:
            application = self.repo.add_application({
                "job_id": job_id,
                "candidate_id": candidate_id,
                "status": "applied",
                "cover_letter": cover_letter,
            })
            if job and job.get("posted_by"):
                self.notifications.create(
                    job["posted_by"],
                    f"A candidate applied for {job.get('title', 'your job')}.",
                    "application",
                )
            self.audit.record(candidate_id, "application.created", "application", application["id"])
            return application
        except DuplicateKeyError as exc:
            raise ValueError("You have already applied for this job.") from exc

    def candidate_applications(self, candidate_id):
        return self.repo.by_candidate(candidate_id)

    def job_applications(self, job_id):
        return self.repo.by_job(job_id)

    def update_status(self, application_id, recruiter_id, status):
        allowed_statuses = {"reviewing", "shortlisted", "rejected", "hired"}
        if not isinstance(status, str) or status not in allowed_statuses:
            raise ValueError("Choose a valid application status.")
        application = self.repo.find_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")
        job = self.job_repo.find_by_id(application["job_id"])
        if not job or job.get("posted_by") != recruiter_id:
            raise PermissionError("You cannot manage this application.")
        updated = self.repo.update_status(application_id, status)
        self.notifications.create(
            application["candidate_id"],
            f"Your application status was updated to {status}.",
            "application",
        )
        self.audit.record(recruiter_id, "application.status_updated", "application", application_id, {"status": status})
        return updated
