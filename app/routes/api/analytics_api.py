from flask import Blueprint, jsonify

from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService
from app.utils.api_auth import api_roles_required

analytics_api_bp = Blueprint("analytics_api", __name__, url_prefix="/api")


@analytics_api_bp.route("/analytics", methods=["GET"])
@api_roles_required("admin")
def analytics():
    service = AnalyticsService()
    return jsonify({"metrics": service.dashboard_metrics(), "application_trend": service.applicant_trend()})


@analytics_api_bp.route("/reports", methods=["GET"])
@api_roles_required("admin")
def reports():
    return jsonify({"report": ReportService().generate()})
