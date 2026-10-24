from app.routes.api.application_api import application_api_bp
from app.routes.api.auth_api import auth_api_bp
from app.routes.api.job_api import job_api_bp
from app.routes.api.candidate_api import candidate_api_bp
from app.routes.api.recruiter_api import recruiter_api_bp
from app.routes.api.interview_api import interview_api_bp
from app.routes.api.resume_api import resume_api_bp
from app.routes.api.analytics_api import analytics_api_bp
from app.routes.api.admin_api import admin_api_bp

api_blueprints = [
    auth_api_bp,
    job_api_bp,
    application_api_bp,
    candidate_api_bp,
    recruiter_api_bp,
    interview_api_bp,
    resume_api_bp,
    analytics_api_bp,
    admin_api_bp,
]
