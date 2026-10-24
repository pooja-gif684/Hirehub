from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    def create_user(self, data):
        return self.insert_one(data)

    def get_by_email(self, email):
        return self.find_one(email=email)

    def get_by_id(self, user_id):
        return self.find_by_id(user_id)

    def list_users(self):
        return self.find_all()
