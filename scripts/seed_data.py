from app import create_app
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    user_repo = UserRepository()
    job_repo = JobRepository()

    if not user_repo.get_by_email("candidate@example.com"):
        user_repo.create_user({
            "id": "candidate-demo",
            "first_name": "Aisha",
            "last_name": "Rahman",
            "email": "candidate@example.com",
            "password_hash": generate_password_hash("CandidateDemo123!"),
            "role": "candidate",
        })
    if not user_repo.get_by_email("recruiter@example.com"):
        user_repo.create_user({
            "id": "recruiter-demo",
            "first_name": "Daniel",
            "last_name": "Nash",
            "email": "recruiter@example.com",
            "password_hash": generate_password_hash("RecruiterDemo123!"),
            "role": "recruiter",
        })

    if not job_repo.find_by_id("job-001"):
        job_repo.create_job({
            "id": "job-001",
            "title": "Senior Python Developer",
            "company": "NovaStack",
            "location": "Remote",
            "job_type": "full-time",
            "salary": "$120k-$150k",
            "category": "Engineering",
            "description": "Build core backend services with Python, Flask, and MongoDB.",
            "requirements": ["Python", "Flask", "MongoDB", "REST APIs"],
            "posted_by": "recruiter-demo",
        })
    if not job_repo.find_by_id("job-002"):
        job_repo.create_job({
            "id": "job-002",
            "title": "Frontend Engineer",
            "company": "Northwind Labs",
            "location": "New York",
            "job_type": "hybrid",
            "salary": "$100k-$130k",
            "category": "Design & Engineering",
            "description": "Shape responsive UI and developer experience for customer-facing applications.",
            "requirements": ["JavaScript", "Bootstrap", "HTML", "CSS"],
            "posted_by": "recruiter-demo",
        })

print("Seed data complete. Demo candidate: candidate@example.com / CandidateDemo123!")
print("Demo recruiter: recruiter@example.com / RecruiterDemo123!")
