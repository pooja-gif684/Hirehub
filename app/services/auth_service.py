from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.errors import DuplicateKeyError
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo=None):
        self.user_repo = user_repo or UserRepository()

    def register(self, payload):
        raw_email = payload.get("email")
        password = payload.get("password")
        first_name = payload.get("first_name", "")
        last_name = payload.get("last_name", "")
        if not isinstance(raw_email, str) or not isinstance(password, str):
            raise ValueError("A valid email address and password are required.")
        if not isinstance(first_name, str) or not isinstance(last_name, str):
            raise ValueError("First and last name must be text.")
        email = raw_email.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        role = payload.get("role", "candidate")
        if not isinstance(role, str) or role not in {"candidate", "recruiter"}:
            raise ValueError("Registration is only available for candidates and recruiters.")
        if self.user_repo.get_by_email(email):
            raise ValueError("A user with that email already exists.")

        user = {
            "id": payload.get("id") or email,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": role,
        }
        try:
            return self.user_repo.create_user(user)
        except DuplicateKeyError as exc:
            raise ValueError("A user with that email already exists.") from exc

    def login(self, email, password):
        if not isinstance(email, str) or not isinstance(password, str):
            raise ValueError("Invalid email or password.")
        user = self.user_repo.get_by_email((email or "").strip().lower())
        if not user or not user.get("active", True) or not check_password_hash(user.get("password_hash", ""), password):
            raise ValueError("Invalid email or password.")
        return user

    def change_password(self, user_id, current_password, new_password):
        if not isinstance(current_password, str) or not isinstance(new_password, str):
            raise ValueError("Current and new passwords are required.")
        user = self.user_repo.get_by_id(user_id)
        if not user or not check_password_hash(user.get("password_hash", ""), current_password):
            raise ValueError("Current password is incorrect.")
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters long.")
        return self.user_repo.update_one(user_id, {
            "password_hash": generate_password_hash(new_password),
        })
