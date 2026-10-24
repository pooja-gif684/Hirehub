from app.repositories.candidate_repository import CandidateRepository


class CandidateService:
    PROFILE_FIELDS = {
        "first_name",
        "last_name",
        "headline",
        "location",
        "skills",
        "experience_years",
        "preferred_roles",
    }
    LIST_FIELDS = {"skills", "preferred_roles"}
    TEXT_FIELDS = PROFILE_FIELDS - LIST_FIELDS - {"experience_years"}

    def __init__(self, repo=None):
        self.repo = repo or CandidateRepository()

    def get_profile(self, candidate_id):
        return self.repo.get_candidate(candidate_id)

    def update_profile(self, candidate_id, data):
        if not isinstance(data, dict):
            raise ValueError("A valid profile is required.")
        updates = {key: value for key, value in data.items() if key in self.PROFILE_FIELDS}
        for field in self.TEXT_FIELDS:
            if field in updates and not isinstance(updates[field], str):
                raise ValueError(f"{field.replace('_', ' ').title()} must be text.")
        for field in self.LIST_FIELDS:
            if field in updates and (
                not isinstance(updates[field], list)
                or not all(isinstance(item, str) for item in updates[field])
            ):
                raise ValueError(f"{field.replace('_', ' ').title()} must be a list of strings.")
        if "experience_years" in updates and (
            isinstance(updates["experience_years"], bool)
            or not isinstance(updates["experience_years"], int)
            or updates["experience_years"] < 0
        ):
            raise ValueError("Experience years must be a non-negative integer.")
        updated = self.repo.update_profile(candidate_id, updates)
        if not updated:
            raise ValueError("Candidate not found.")
        return updated
