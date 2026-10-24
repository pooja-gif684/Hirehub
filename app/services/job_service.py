from app.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, repo=None):
        self.repo = repo or JobRepository()

    def list_jobs(self, filters=None):
        filters = filters or {}
        return self.repo.filter_jobs(
            query=filters.get("query"),
            location=filters.get("location"),
            category=filters.get("category"),
            job_type=filters.get("job_type")
        )

    def create_job(self, data):
        required = ("title", "company", "location", "description")
        if any(not isinstance(data.get(field), str) or not data[field].strip() for field in required):
            raise ValueError("Title, company, location, and description are required.")
        for field in ("job_type", "salary", "category"):
            if field in data and not isinstance(data[field], str):
                raise ValueError(f"{field.title()} must be text.")
        requirements = data.get("requirements", [])
        if not isinstance(requirements, list) or not all(isinstance(item, str) for item in requirements):
            raise ValueError("Job requirements must be a list of strings.")
        return self.repo.create_job(data)

    def get_job(self, job_id):
        return self.repo.find_by_id(job_id)

    def update_job(self, job_id, recruiter_id, data):
        job = self.repo.find_by_id(job_id)
        if not job:
            raise ValueError("Job not found.")
        if job.get("posted_by") != recruiter_id:
            raise PermissionError("You cannot edit this job.")
        updates = {key: value for key, value in data.items() if key in {
            "title", "company", "location", "job_type", "salary",
            "category", "description", "requirements", "status",
        }}
        if "title" in updates and (not isinstance(updates["title"], str) or not updates["title"].strip()):
            raise ValueError("Job title is required.")
        if "status" in updates and (not isinstance(updates["status"], str) or updates["status"] not in {"open", "closed"}):
            raise ValueError("Job status must be open or closed.")
        if "requirements" in updates and (
            not isinstance(updates["requirements"], list)
            or not all(isinstance(item, str) for item in updates["requirements"])
        ):
            raise ValueError("Job requirements must be a list of strings.")
        for field in ("company", "location", "description"):
            if field in updates and (not isinstance(updates[field], str) or not updates[field].strip()):
                raise ValueError(f"{field.title()} cannot be empty.")
        for field in ("job_type", "salary", "category"):
            if field in updates and not isinstance(updates[field], str):
                raise ValueError(f"{field.title()} must be text.")
        return self.repo.update_one(job_id, updates)

    def delete_job(self, job_id, recruiter_id):
        job = self.repo.find_by_id(job_id)
        if not job:
            raise ValueError("Job not found.")
        if job.get("posted_by") != recruiter_id:
            raise PermissionError("You cannot delete this job.")
        return self.repo.delete_one(job_id)
