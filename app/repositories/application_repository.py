from app.repositories.base_repository import BaseRepository


class ApplicationRepository(BaseRepository):
    def __init__(self):
        super().__init__("applications")

    def add_application(self, data):
        return self.insert_one(data)

    def by_candidate(self, candidate_id):
        return self.find_all({"candidate_id": candidate_id})

    def by_job(self, job_id):
        return self.find_all({"job_id": job_id})

    def update_status(self, application_id, status):
        return self.update_one(application_id, {"status": status})
