from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository


class CompanyService:
    def __init__(self, repo=None, user_repo=None):
        self.repo = repo or CompanyRepository()
        self.user_repo = user_repo or UserRepository()

    def get_for_recruiter(self, recruiter_id):
        recruiter = self.user_repo.get_by_id(recruiter_id)
        if not recruiter or recruiter.get("role") != "recruiter":
            return None
        return self.repo.get_for_recruiter(recruiter_id)

    def update_for_recruiter(self, recruiter_id, data):
        if not isinstance(data, dict):
            raise ValueError("A valid company profile is required.")
        recruiter = self.user_repo.get_by_id(recruiter_id)
        if not recruiter or recruiter.get("role") != "recruiter":
            raise ValueError("Recruiter not found.")

        updates = {key: value for key, value in data.items() if key in {"name", "position", "location"}}
        for field, value in updates.items():
            if not isinstance(value, str):
                raise ValueError(f"{field.title()} must be text.")
            updates[field] = value.strip()
        existing = self.repo.get_for_recruiter(recruiter_id)
        if "name" in updates and not updates["name"].strip():
            self.repo.delete_for_recruiter(recruiter_id)
            user_updates = {"company": ""}
            if "position" in updates:
                user_updates["position"] = updates["position"]
            self.user_repo.update_one(recruiter_id, user_updates)
            return None

        if not updates:
            return existing
        if not existing and "name" not in updates:
            raise ValueError("Company name is required.")

        company = self.repo.save_for_recruiter(recruiter_id, updates)
        user_updates = {}
        if "name" in updates:
            user_updates["company"] = updates["name"].strip()
        if "position" in updates:
            user_updates["position"] = updates["position"].strip()
        if "location" in updates:
            user_updates["location"] = updates["location"].strip()
        if user_updates:
            self.user_repo.update_one(recruiter_id, user_updates)
        return company
