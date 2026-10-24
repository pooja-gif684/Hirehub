from datetime import datetime, timezone
from uuid import uuid4

from pymongo import ReturnDocument

from app.models import CompanyDocument
from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository):
    def __init__(self):
        super().__init__("companies")

    def get_for_recruiter(self, recruiter_id) -> CompanyDocument | None:
        return self.find_one(recruiter_id=recruiter_id)

    def save_for_recruiter(self, recruiter_id, data) -> CompanyDocument:
        now = datetime.now(timezone.utc).isoformat()
        updates = dict(data)
        updates.pop("id", None)
        updates.pop("recruiter_id", None)
        updates["updated_at"] = now
        record = self.collection.find_one_and_update(
            {"recruiter_id": recruiter_id},
            {
                "$set": updates,
                "$setOnInsert": {
                    "id": str(uuid4()),
                    "recruiter_id": recruiter_id,
                    "created_at": now,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return self._clean(record)

    def delete_for_recruiter(self, recruiter_id) -> CompanyDocument | None:
        return self._clean(self.collection.find_one_and_delete({"recruiter_id": recruiter_id}))
