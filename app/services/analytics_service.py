from collections import Counter
from datetime import datetime

from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.repositories.interview_repository import InterviewRepository


class AnalyticsService:
    def __init__(self, app_repo=None, job_repo=None, user_repo=None):
        self.app_repo = app_repo or ApplicationRepository()
        self.job_repo = job_repo or JobRepository()
        self.user_repo = user_repo or UserRepository()

    def dashboard_metrics(self):
        users = self.user_repo.list_users()
        jobs = self.job_repo.list_jobs()
        apps = self.app_repo.find_all()
        return {
            "total_users": len(users),
            "total_jobs": len(jobs),
            "total_applications": len(apps),
            "total_interviews": InterviewRepository().count(),
            "candidate_count": len([u for u in users if u.get("role") == "candidate"]),
            "recruiter_count": len([u for u in users if u.get("role") == "recruiter"]),
            "admin_count": len([u for u in users if u.get("role") == "admin"]),
        }

    def applicant_trend(self):
        counts = Counter()
        for application in self.app_repo.find_all():
            try:
                created = datetime.fromisoformat(application["created_at"])
            except (KeyError, TypeError, ValueError):
                continue
            counts[created.strftime("%Y-%m")] += 1
        return [{"month": month, "applications": counts[month]} for month in sorted(counts)[-12:]]
