from typing import TypedDict


class BaseDocument(TypedDict, total=False):
    id: str
    created_at: str
    updated_at: str


class UserDocument(BaseDocument, total=False):
    email: str
    first_name: str
    last_name: str
    role: str
    active: bool
    password_hash: str


class CandidateDocument(UserDocument, total=False):
    headline: str
    location: str
    skills: list[str]
    experience_years: int
    preferred_roles: list[str]


class CompanyDocument(BaseDocument, total=False):
    recruiter_id: str
    name: str
    position: str
    location: str


class JobDocument(BaseDocument, total=False):
    posted_by: str
    title: str
    company: str
    location: str
    job_type: str
    salary: str
    category: str
    description: str
    requirements: list[str]
    status: str


class ApplicationDocument(BaseDocument, total=False):
    job_id: str
    candidate_id: str
    status: str
    cover_letter: str


class InterviewDocument(BaseDocument, total=False):
    application_id: str
    candidate_id: str
    recruiter_id: str
    scheduled_for: str
    mode: str
    meeting_link: str


class NotificationDocument(BaseDocument, total=False):
    user_id: str
    message: str
    type: str
    is_read: bool


class ResumeDocument(BaseDocument, total=False):
    candidate_id: str
    filename: str
    original_name: str
    storage_path: str
    uploaded_at: str


class AuditLogDocument(BaseDocument, total=False):
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    details: dict
    ip_address: str
