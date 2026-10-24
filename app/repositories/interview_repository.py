from app.repositories.base_repository import BaseRepository


class InterviewRepository(BaseRepository):
    def __init__(self):
        super().__init__("interviews")

    def for_candidate(self, candidate_id):
        return self.collection.find({"candidate_id": candidate_id}).sort("scheduled_for", 1)

    def for_recruiter(self, recruiter_id):
        return self.collection.find({"recruiter_id": recruiter_id}).sort("scheduled_for", 1)

    def list_for_candidate(self, candidate_id):
        return [self._clean(item) for item in self.for_candidate(candidate_id)]

    def list_for_recruiter(self, recruiter_id):
        return [self._clean(item) for item in self.for_recruiter(recruiter_id)]
