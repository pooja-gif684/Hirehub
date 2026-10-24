import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO

from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.company_repository import CompanyRepository
from app.services.application_service import ApplicationService
from werkzeug.security import check_password_hash, generate_password_hash


def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_jobs_page(client):
    response = client.get('/jobs')
    assert response.status_code == 200


def test_register_page(client):
    response = client.get('/register')
    assert response.status_code == 200


def test_default_admin_can_log_in(client):
    response = client.post('/login', data={
        'email': 'admin@hirehub.local',
        'password': 'HireHubDev@2026!',
    })
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/dashboard')

    dashboard_response = client.get('/dashboard', follow_redirects=True)
    assert dashboard_response.status_code == 200
    assert b'Admin Dashboard' in dashboard_response.data


def test_dashboard_rejects_unknown_session_role(client):
    with client.session_transaction() as session:
        session['user_id'] = 'invalid-user'
        session['user'] = {'id': 'invalid-user', 'role': 'unknown'}

    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data


def test_candidate_can_apply_once_for_existing_job(client):
    job_id = f"job-{uuid.uuid4().hex}"
    JobRepository().create_job({"id": job_id, "title": "Test Engineer"})
    UserRepository().create_user({
        "id": "candidate-test",
        "email": f"candidate-{uuid.uuid4().hex}@example.test",
        "role": "candidate",
    })
    with client.session_transaction() as session:
        session["user_id"] = "candidate-test"
        session["user"] = {"id": "candidate-test", "role": "candidate"}

    detail_response = client.get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    assert b"Apply Now" in detail_response.data

    response = client.post("/api/applications", json={"job_id": job_id})
    assert response.status_code == 201
    assert response.json["application"]["candidate_id"] == "candidate-test"

    tracking_response = client.get("/candidate/applications")
    assert tracking_response.status_code == 200
    assert b"Test Engineer" in tracking_response.data

    duplicate_response = client.post("/api/applications", json={"job_id": job_id})
    assert duplicate_response.status_code == 400
    assert "already applied" in duplicate_response.json["message"]


def test_only_logged_in_candidates_can_apply(client):
    unauthorized = client.post("/api/applications", json={"job_id": "any-job"})
    assert unauthorized.status_code == 401

    UserRepository().create_user({
        "id": "recruiter-test",
        "email": f"recruiter-{uuid.uuid4().hex}@example.test",
        "role": "recruiter",
    })
    with client.session_transaction() as session:
        session["user_id"] = "recruiter-test"
        session["user"] = {"id": "recruiter-test", "role": "recruiter"}
    forbidden = client.post("/api/applications", json={"job_id": "any-job"})
    assert forbidden.status_code == 403


def test_candidate_profile_is_persisted(client):
    user = UserRepository().create_user({
        "id": "candidate-profile-test",
        "first_name": "Before",
        "last_name": "Name",
        "email": "profile@example.test",
        "role": "candidate",
    })
    with client.session_transaction() as session:
        session["user_id"] = user["id"]
        session["user"] = user

    response = client.post("/candidate/profile", data={
        "first_name": "Updated",
        "last_name": "Candidate",
        "headline": "Python Developer",
        "location": "Remote",
        "skills": "Python, Flask",
    })

    assert response.status_code == 200
    persisted_user = UserRepository().get_by_id(user["id"])
    assert persisted_user["first_name"] == "Updated"
    assert persisted_user["skills"] == ["Python", "Flask"]


def test_candidate_service_validates_profile_and_role(client):
    candidate = UserRepository().create_user({
        "id": "candidate-service",
        "email": "candidate-service@example.test",
        "role": "candidate",
    })
    recruiter = UserRepository().create_user({
        "id": "candidate-service-recruiter",
        "email": "candidate-service-recruiter@example.test",
        "role": "recruiter",
    })
    candidates = CandidateRepository()

    assert candidates.get_candidate(candidate["id"])["id"] == candidate["id"]
    assert candidates.get_candidate(recruiter["id"]) is None

    with client.session_transaction() as session:
        session["user_id"] = candidate["id"]
        session["user"] = candidate
    response = client.patch("/api/candidate/profile", json={"skills": "Python"})
    assert response.status_code == 400

    updated = client.patch("/api/candidate/profile", json={
        "skills": ["Python", "Flask"],
        "experience_years": 3,
        "preferred_roles": ["Backend Engineer"],
    })
    assert updated.status_code == 200
    stored = candidates.get_candidate(candidate["id"])
    assert stored["skills"] == ["Python", "Flask"]
    assert stored["experience_years"] == 3


def test_recruiter_company_profile_is_persisted(client):
    recruiter = UserRepository().create_user({
        "id": "company-recruiter",
        "email": "company-recruiter@example.test",
        "role": "recruiter",
    })
    with client.session_transaction() as session:
        session["user_id"] = recruiter["id"]
        session["user"] = recruiter

    response = client.patch("/api/recruiter/company", json={
        "name": "HireHub Labs",
        "position": "Talent Lead",
        "location": "Remote",
    })
    assert response.status_code == 200
    company = CompanyRepository().get_for_recruiter(recruiter["id"])
    assert company["name"] == "HireHub Labs"
    assert company["position"] == "Talent Lead"
    stored_user = UserRepository().get_by_id(recruiter["id"])
    assert stored_user["company"] == company["name"]
    assert client.get("/api/recruiter/company").json["company"]["id"] == company["id"]

    updated = client.patch("/api/recruiter/company", json={"name": "HireHub Group"})
    assert updated.status_code == 200
    assert updated.json["company"]["id"] == company["id"]
    assert CompanyRepository().find_all({"recruiter_id": recruiter["id"]})[0]["name"] == "HireHub Group"


def test_registration_hashes_password_and_login_session_is_safe(client):
    register = client.post("/register", data={
        "first_name": "New",
        "last_name": "Candidate",
        "email": "new.candidate@example.test",
        "password": "secure-password-123",
        "role": "candidate",
    })
    assert register.status_code == 302
    account = UserRepository().get_by_email("new.candidate@example.test")
    assert account["password_hash"] != "secure-password-123"

    login = client.post("/login", data={
        "email": "new.candidate@example.test",
        "password": "secure-password-123",
    })
    assert login.status_code == 302
    with client.session_transaction() as session:
        assert session["user"]["id"] == account["id"]
        assert "password_hash" not in session["user"]

    cookie = login.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_candidate_resume_upload_and_private_download(client):
    user = UserRepository().create_user({
        "id": "resume-candidate",
        "email": "resume@example.test",
        "role": "candidate",
    })
    with client.session_transaction() as session:
        session["user_id"] = user["id"]
        session["user"] = user

    upload = client.post(
        "/candidate/resume",
        data={"resume": (BytesIO(b"resume test content"), "candidate.pdf")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 200
    from app.repositories.resume_repository import ResumeRepository
    resume = ResumeRepository().for_candidate(user["id"])[0]
    download = client.get(f"/candidate/resume/{resume['id']}/download")
    assert download.status_code == 200
    assert download.data == b"resume test content"


def test_resume_api_upload_download_and_candidate_ownership(client):
    candidate = UserRepository().create_user({
        "id": "resume-api-candidate",
        "email": "resume-api@example.test",
        "role": "candidate",
    })
    other_candidate = UserRepository().create_user({
        "id": "resume-api-other",
        "email": "resume-api-other@example.test",
        "role": "candidate",
    })
    with client.session_transaction() as session:
        session["user_id"] = candidate["id"]
        session["user"] = candidate

    upload = client.post(
        "/api/resumes",
        data={"resume": (BytesIO(b"API resume content"), "api-candidate.pdf")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    resume = upload.json["resume"]
    assert "storage_path" not in resume
    assert client.get("/api/resumes").status_code == 200
    download = client.get(f"/api/resumes/{resume['id']}/download")
    assert download.status_code == 200
    assert download.data == b"API resume content"

    with client.session_transaction() as session:
        session["user_id"] = other_candidate["id"]
        session["user"] = other_candidate
    denied = client.get(f"/api/resumes/{resume['id']}/download")
    assert denied.status_code == 404


def test_recruiter_can_review_application_schedule_interview_and_notify_candidate(client):
    recruiter = UserRepository().create_user({
        "id": "recruiter-flow",
        "email": "recruiter-flow@example.test",
        "role": "recruiter",
    })
    candidate = UserRepository().create_user({
        "id": "candidate-flow",
        "email": "candidate-flow@example.test",
        "role": "candidate",
    })
    job = JobRepository().create_job({
        "id": "job-flow",
        "title": "Recruitment Engineer",
        "posted_by": recruiter["id"],
    })
    application = ApplicationService().apply_for_job(job["id"], candidate["id"])
    with client.session_transaction() as session:
        session["user_id"] = recruiter["id"]
        session["user"] = recruiter

    status = client.post("/recruiter/applications", data={
        "application_id": application["id"],
        "status": "shortlisted",
    })
    assert status.status_code == 302
    assert ApplicationRepository().find_by_id(application["id"])["status"] == "shortlisted"

    schedule = client.post("/recruiter/interviews", data={
        "application_id": application["id"],
        "scheduled_for": (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
        "mode": "virtual",
        "meeting_link": "https://meet.example.test/interview",
    })
    assert schedule.status_code == 302

    with client.session_transaction() as session:
        session["user_id"] = candidate["id"]
        session["user"] = candidate
    response = client.get("/candidate/notifications")
    assert response.status_code == 200
    assert b"interview" in response.data
    assert client.get("/candidate/interviews").status_code == 200


def test_admin_can_access_management_and_reports(client):
    login = client.post("/login", data={
        "email": "admin@hirehub.local",
        "password": "HireHubDev@2026!",
    })
    assert login.status_code == 302
    for path in (
        "/admin/users",
        "/admin/jobs",
        "/admin/applications",
        "/admin/interviews",
        "/admin/reports",
        "/admin/audit-logs",
    ):
        assert client.get(path).status_code == 200
    assert client.get("/api/analytics").status_code == 200
    assert client.get("/api/reports").status_code == 200


def test_recruiter_job_api_enforces_ownership(client):
    recruiter = UserRepository().create_user({
        "id": "api-recruiter",
        "email": "api-recruiter@example.test",
        "role": "recruiter",
    })
    other_recruiter = UserRepository().create_user({
        "id": "api-other-recruiter",
        "email": "api-other-recruiter@example.test",
        "role": "recruiter",
    })
    with client.session_transaction() as session:
        session["user_id"] = recruiter["id"]
        session["user"] = recruiter

    created = client.post("/api/jobs", json={
        "title": "Backend Engineer",
        "company": "HireHub",
        "location": "Remote",
        "description": "Build backend services.",
    })
    assert created.status_code == 201
    job_id = created.json["job"]["id"]
    assert created.json["job"]["posted_by"] == recruiter["id"]

    with client.session_transaction() as session:
        session["user_id"] = other_recruiter["id"]
        session["user"] = other_recruiter
    forbidden = client.patch(f"/api/jobs/{job_id}", json={"title": "Changed"})
    assert forbidden.status_code == 403


def test_recommendations_use_candidate_profile_skills(client):
    candidate = UserRepository().create_user({
        "id": "skilled-candidate",
        "email": "skilled@example.test",
        "role": "candidate",
        "skills": ["python", "mongodb"],
    })
    JobRepository().create_job({
        "id": "python-match",
        "title": "Python Engineer",
        "description": "Develop services",
        "requirements": ["Python", "MongoDB"],
    })
    JobRepository().create_job({
        "id": "design-match",
        "title": "Product Designer",
        "description": "Design user journeys",
        "requirements": ["Figma"],
    })
    with client.session_transaction() as session:
        session["user_id"] = candidate["id"]
        session["user"] = candidate

    response = client.get("/api/candidate/recommendations")
    assert response.status_code == 200
    ids = [job["id"] for job in response.json["recommendations"]]
    assert "python-match" in ids
    assert "design-match" not in ids


def test_api_auth_sets_and_clears_session(client):
    register = client.post("/api/auth/register", json={
        "first_name": "API",
        "last_name": "Candidate",
        "email": "api-candidate@example.test",
        "password": "api-password-123",
        "role": "candidate",
    })
    assert register.status_code == 201
    assert "password_hash" not in register.json["user"]

    login = client.post("/api/auth/login", json={
        "email": "api-candidate@example.test",
        "password": "api-password-123",
    })
    assert login.status_code == 200
    assert client.get("/api/candidate/profile").status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert client.get("/api/candidate/profile").status_code == 401


def test_password_change_requires_current_password(client):
    user = UserRepository().create_user({
        "id": "password-candidate",
        "email": "password@example.test",
        "password_hash": generate_password_hash("old-password-123"),
        "role": "candidate",
    })
    with client.session_transaction() as session:
        session["user_id"] = user["id"]
        session["user"] = {key: value for key, value in user.items() if key != "password_hash"}

    rejected = client.post("/profile", data={
        "current_password": "wrong-password",
        "new_password": "new-password-123",
    })
    assert rejected.status_code == 400

    accepted = client.post("/profile", data={
        "current_password": "old-password-123",
        "new_password": "new-password-123",
    })
    assert accepted.status_code == 200
    persisted = UserRepository().get_by_id(user["id"])
    assert check_password_hash(persisted["password_hash"], "new-password-123")


def test_disabled_user_session_is_rejected(client):
    user = UserRepository().create_user({
        "id": "disabled-candidate",
        "email": "disabled@example.test",
        "role": "candidate",
    })
    with client.session_transaction() as session:
        session["user_id"] = user["id"]
        session["user"] = user
    UserRepository().update_one(user["id"], {"active": False})

    response = client.get("/candidate/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
