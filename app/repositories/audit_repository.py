from app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository):
    def __init__(self):
        super().__init__("audit_logs")

    def recent(self, limit=100):
        records = self.collection.find({}).sort("created_at", -1).limit(limit)
        return [self._clean(record) for record in records]
