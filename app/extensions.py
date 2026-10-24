from flask import Flask
from pymongo import MongoClient


class MongoExtension:
    client = None
    db = None

    def init_app(self, app: Flask):
        configured_client = app.config.get("MONGO_CLIENT")
        self.client = configured_client if configured_client is not None else MongoClient(
            app.config["MONGO_URI"],
            serverSelectionTimeoutMS=app.config.get("MONGO_TIMEOUT_MS", 5000),
        )
        self.db = self.client[app.config["MONGO_DBNAME"]]
        self.client.admin.command("ping")
        self.db.users.create_index("id", unique=True)
        self.db.users.create_index("email", unique=True)
        self.db.jobs.create_index("id", unique=True)
        self.db.applications.create_index("id", unique=True)
        self.db.applications.create_index(
            [("job_id", 1), ("candidate_id", 1)],
            unique=True,
        )
        self.db.interviews.create_index("id", unique=True)
        self.db.interviews.create_index([("candidate_id", 1), ("scheduled_for", 1)])
        self.db.notifications.create_index("id", unique=True)
        self.db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        self.db.companies.create_index("id", unique=True)
        self.db.companies.create_index("recruiter_id", unique=True)
        self.db.resumes.create_index("id", unique=True)
        self.db.audit_logs.create_index("id", unique=True)
        self.db.audit_logs.create_index([("created_at", -1)])

    def collection(self, name):
        return self.db[name]


mongo = MongoExtension()
