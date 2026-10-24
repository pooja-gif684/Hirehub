from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self):
        super().__init__("notifications")

    def for_user(self, user_id):
        records = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        return [self._clean(record) for record in records]
