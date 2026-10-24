from functools import wraps

from flask import jsonify, session

from app.repositories.user_repository import UserRepository


def api_roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            user = UserRepository().get_by_id(user_id) if user_id else None
            if not user or not user.get("active", True):
                session.clear()
                return jsonify({"status": "error", "message": "Authentication required."}), 401
            safe_user = {key: value for key, value in user.items() if key != "password_hash"}
            session["user"] = safe_user
            if roles and safe_user.get("role") not in roles:
                return jsonify({"status": "error", "message": "Insufficient permissions."}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator
