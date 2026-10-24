from flask import has_request_context, request

from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, repo=None):
        self.repo = repo or AuditRepository()

    def record(self, actor_id, action, resource_type, resource_id="", details=None):
        ip_address = request.remote_addr if has_request_context() else ""
        return self.repo.insert_one({
            "actor_id": actor_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
        })

    def recent(self, limit=100):
        return self.repo.recent(limit)
