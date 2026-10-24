from flask import Blueprint, jsonify, request, session
from urllib.parse import urlparse

from app.services.audit_service import AuditService
from app.services.interview_service import InterviewService
from app.utils.api_auth import api_roles_required

interview_api_bp = Blueprint("interview_api", __name__, url_prefix="/api")


@interview_api_bp.route("/interviews", methods=["POST"])
@api_roles_required("recruiter")
def schedule():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "A valid JSON request is required."}), 400
    meeting_link = payload.get("meeting_link", "")
    if meeting_link and urlparse(meeting_link).scheme not in {"https", "http"}:
        return jsonify({"status": "error", "message": "Meeting link must use HTTP or HTTPS."}), 400
    try:
        interview = InterviewService().schedule(payload, session["user"]["id"])
        AuditService().record(session["user"]["id"], "interview.scheduled", "interview", interview["id"])
        return jsonify({"interview": interview}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 403


@interview_api_bp.route("/interviews", methods=["GET"])
@api_roles_required("recruiter", "admin")
def list_interviews():
    service = InterviewService()
    if session["user"]["role"] == "admin":
        items = service.all()
    else:
        items = service.for_recruiter(session["user"]["id"])
    return jsonify({"interviews": items})
