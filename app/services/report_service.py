from collections import Counter

from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.repositories.interview_repository import InterviewRepository


class ReportService:
    def __init__(self, user_repo=None, job_repo=None, application_repo=None, interview_repo=None):
        self.users = user_repo or UserRepository()
        self.jobs = job_repo or JobRepository()
        self.applications = application_repo or ApplicationRepository()
        self.interviews = interview_repo or InterviewRepository()

    def generate(self):
        users = self.users.list_users()
        jobs = self.jobs.list_jobs()
        applications = self.applications.find_all()
        status_counts = Counter(item.get("status", "unknown") for item in applications)
        return {
            "total_users": len(users),
            "users_by_role": dict(Counter(item.get("role", "unknown") for item in users)),
            "total_jobs": len(jobs),
            "total_applications": len(applications),
            "total_interviews": self.interviews.count(),
            "applications_by_status": dict(status_counts),
            "applications_per_job": [
                {
                    "job_title": next((job.get("title", "Job") for job in jobs if job.get("id") == job_id), "Job"),
                    "applications": sum(1 for item in applications if item.get("job_id") == job_id),
                }
                for job_id in dict.fromkeys(item.get("job_id") for item in applications)
            ],
        }
