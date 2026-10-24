from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, repo=None):
        self.repo = repo or NotificationRepository()

    def create(self, user_id, message, notification_type="info"):
        return self.repo.insert_one({
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "is_read": False,
        })

    def for_user(self, user_id):
        return self.repo.for_user(user_id)

    def mark_read(self, notification_id, user_id):
        notification = self.repo.find_by_id(notification_id)
        if not notification:
            raise ValueError("Notification not found.")
        if notification.get("user_id") != user_id:
            raise PermissionError("You cannot update this notification.")
        updated = self.repo.update_one(notification_id, {"is_read": True})
        return updated

    def mark_all_read(self, user_id):
        self.repo.collection.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}},
        )

