from app.repositories.base_repository import BaseRepository


class ResumeRepository(BaseRepository):
    def __init__(self):
        super().__init__("resumes")

    def for_candidate(self, candidate_id):
        records = self.collection.find({"candidate_id": candidate_id}).sort("uploaded_at", -1)
        return [self._clean(record) for record in records]
