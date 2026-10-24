import os
from datetime import timedelta
from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "hirehub-dev-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/hirehub")
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "hirehub")
    MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "5000"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/uploads/resumes")
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@hirehub.local")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "HireHubDev@2026!")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
