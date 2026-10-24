import re

from app.repositories.base_repository import BaseRepository


class JobRepository(BaseRepository):
    def __init__(self):
        super().__init__("jobs")

    def list_jobs(self):
        return self.find_all()

    def create_job(self, data):
        return self.insert_one(data)

    def filter_jobs(self, query=None, location=None, category=None, job_type=None):
        filters = {"status": {"$ne": "closed"}}
        if query:
            pattern = {"$regex": re.escape(query), "$options": "i"}
            filters["$or"] = [
                {"title": pattern},
                {"description": pattern},
                {"company": pattern},
            ]
        if location:
            filters["location"] = {"$regex": re.escape(location), "$options": "i"}
        if category:
            filters["category"] = {"$regex": re.escape(category), "$options": "i"}
        if job_type:
            filters["job_type"] = {"$regex": re.escape(job_type), "$options": "i"}
        return self.find_all(filters)

    def by_recruiter(self, recruiter_id):
        return self.find_all({"posted_by": recruiter_id})
