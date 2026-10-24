from flask import Flask, redirect, session, url_for
from app.config import Config
from app.extensions import mongo
from app.repositories.user_repository import UserRepository
from app.routes import register_blueprints
from werkzeug.security import generate_password_hash


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    mongo.init_app(app)
    register_blueprints(app)

    user_repository = UserRepository()
    admin_email = app.config["DEFAULT_ADMIN_EMAIL"].strip().lower()
    if not user_repository.get_by_email(admin_email):
        user_repository.create_user({
            "id": admin_email,
            "first_name": "HireHub",
            "last_name": "Admin",
            "email": admin_email,
            "password_hash": generate_password_hash(app.config["DEFAULT_ADMIN_PASSWORD"]),
            "role": "admin",
        })

    @app.route("/")
    def index():
        if "user" in session:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    return app
