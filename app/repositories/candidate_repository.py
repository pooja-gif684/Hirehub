from app.models import CandidateDocument
from app.repositories.user_repository import UserRepository


class CandidateRepository(UserRepository):
    def get_candidate(self, candidate_id) -> CandidateDocument | None:
        candidate = self.get_by_id(candidate_id)
        return candidate if candidate and candidate.get("role") == "candidate" else None

    def list_candidates(self) -> list[CandidateDocument]:
        return self.find_all({"role": "candidate"})

    def update_profile(self, candidate_id, updates) -> CandidateDocument | None:
        if not self.get_candidate(candidate_id):
            return None
        return self.update_one(candidate_id, updates)
