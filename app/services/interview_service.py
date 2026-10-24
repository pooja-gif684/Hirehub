from datetime import datetime, timezone
from urllib.parse import urlparse

from app.repositories.application_repository import ApplicationRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.services.notification_service import NotificationService


class InterviewService:
    def __init__(self, interview_repo=None, application_repo=None, job_repo=None, notifications=None):
        self.interviews = interview_repo or InterviewRepository()
        self.applications = application_repo or ApplicationRepository()
        self.jobs = job_repo or JobRepository()
        self.notifications = notifications or NotificationService()

    def schedule(self, payload, recruiter_id):
        application_id = payload.get("application_id")
        if not isinstance(application_id, str) or not application_id:
            raise ValueError("Select an application for the interview.")
        scheduled_for = payload.get("scheduled_for", "")
        if not isinstance(scheduled_for, str):
            raise ValueError("Enter a valid interview date and time.")
        scheduled_for = scheduled_for.strip()
        try:
            scheduled = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Enter a valid interview date and time.") from exc
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=timezone.utc)
        if scheduled <= datetime.now(timezone.utc):
            raise ValueError("Interview time must be in the future.")
        mode = payload.get("mode") or "virtual"
        if not isinstance(mode, str) or mode.strip() not in {"virtual", "in-person", "phone"}:
            raise ValueError("Choose a valid interview format.")
        mode = mode.strip()
        meeting_link = payload.get("meeting_link", "")
        if not isinstance(meeting_link, str):
            raise ValueError("Meeting link must be text.")
        meeting_link = meeting_link.strip()
        if meeting_link and urlparse(meeting_link).scheme not in {"https", "http"}:
            raise ValueError("Meeting link must use HTTP or HTTPS.")

        application = self.applications.find_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")
        job = self.jobs.find_by_id(application["job_id"])
        if not job or job.get("posted_by") != recruiter_id:
            raise PermissionError("You cannot schedule an interview for this application.")
        interview = self.interviews.insert_one({
            "application_id": application_id,
            "job_id": job["id"],
            "candidate_id": application["candidate_id"],
            "recruiter_id": recruiter_id,
            "scheduled_for": scheduled.isoformat(),
            "mode": mode,
            "meeting_link": meeting_link,
            "status": "scheduled",
        })
        self.notifications.create(
            application["candidate_id"],
            f"An interview for {job.get('title', 'your application')} has been scheduled for {scheduled.isoformat()}.",
            "interview",
        )
        return interview

    def for_candidate(self, candidate_id):
        return self.interviews.list_for_candidate(candidate_id)

    def for_recruiter(self, recruiter_id):
        return self.interviews.list_for_recruiter(recruiter_id)

    def all(self):
        return self.interviews.find_all()
