import uuid
from datetime import datetime, timezone

from app.extensions import mongo


class BaseRepository:
    def __init__(self, collection_name):
        self.collection_name = collection_name

    @property
    def collection(self):
        return mongo.collection(self.collection_name)

    def _normalize(self, data):
        payload = dict(data)
        payload.setdefault("id", str(uuid.uuid4()))
        now = datetime.now(timezone.utc).isoformat()
        payload.setdefault("created_at", now)
        payload.setdefault("updated_at", now)
        return payload

    @staticmethod
    def _clean(record):
        if record is None:
            return None
        record.pop("_id", None)
        return record

    def insert_one(self, payload):
        record = self._normalize(payload)
        self.collection.insert_one(record.copy())
        return record

    def find_all(self, filters=None):
        return [self._clean(record) for record in self.collection.find(filters or {})]

    def find_by_id(self, item_id):
        return self._clean(self.collection.find_one({"id": item_id}))

    def find_one(self, **filters):
        return self._clean(self.collection.find_one(filters))

    def update_one(self, item_id, payload):
        updates = dict(payload)
        updates.pop("_id", None)
        updates.pop("id", None)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = self.collection.update_one({"id": item_id}, {"$set": updates})
        if result.matched_count == 0:
            return None
        return self.find_by_id(item_id)

    def delete_one(self, item_id):
        return self._clean(self.collection.find_one_and_delete({"id": item_id}))

    def count(self):
        return self.collection.count_documents({})
