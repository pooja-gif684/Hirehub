from app.routes.web.admin_routes import admin_bp
from app.routes.web.auth_routes import auth_bp
from app.routes.web.candidate_routes import candidate_bp
from app.routes.web.dashboard_routes import dashboard_bp
from app.routes.web.job_routes import job_bp
from app.routes.web.recruiter_routes import recruiter_bp

web_blueprints = [auth_bp, dashboard_bp, candidate_bp, recruiter_bp, admin_bp, job_bp]
