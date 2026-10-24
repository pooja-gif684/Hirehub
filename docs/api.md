# HireHub REST API

All endpoints are under `/api`. Authentication uses the same session cookie as the web UI. Login sets the cookie; logout clears it. Authenticated write operations require the corresponding role.

## Authentication

- `POST /api/auth/register` — create a candidate or recruiter account
- `POST /api/auth/login` — authenticate and create a session
- `POST /api/auth/logout` — clear the current session

## Jobs

- `GET /api/jobs` — search with optional `query`, `location`, `category`, and `job_type` parameters
- `GET /api/jobs/<job_id>` — job details
- `POST /api/jobs` — recruiter/admin create a posting
- `PATCH /api/jobs/<job_id>` and `DELETE /api/jobs/<job_id>` — owner/admin job management
- `GET /api/recruiter/jobs` — current recruiter's postings
- `GET /api/recruiter/company` and `PATCH /api/recruiter/company` — read/update the recruiter's company profile

## Candidate

- `GET` / `PATCH /api/candidate/profile` — read/update profile and change password with current/new password fields
- `GET /api/candidate/recommendations` — jobs matched to profile skills
- `GET /api/candidate/applications` and `GET /api/applications/me` — application history
- `GET /api/candidate/interviews` — scheduled interviews
- `GET` / `PATCH /api/candidate/notifications` — notifications and mark-read actions
- `GET` / `PATCH /api/notifications` — current user's notifications

## Applications and recruiting

- `POST /api/applications` — candidate applies using `{ "job_id": "...", "cover_letter": "..." }`
- `GET /api/applications/<job_id>` — owner recruiter/admin application list
- `PATCH /api/applications/<application_id>/status` — owner recruiter updates status
- `GET /api/recruiter/applications` — recruiter application list
- `GET /api/recruiter/notifications` — current recruiter's notifications
- `POST /api/interviews` — recruiter schedules an interview
- `GET /api/interviews` and `GET /api/recruiter/interviews` — interview lists

## Resumes

- `GET` / `POST /api/resumes` — candidate list/upload (multipart field `resume`)
- `GET /api/resumes/<resume_id>/download` — owner candidate, applicant's recruiter, or admin download

## Admin

- `GET /api/analytics` — summary metrics and application trend
- `GET /api/reports` — report summary and application breakdown
- `GET /api/admin/users` and `PATCH /api/admin/users/<user_id>` — user administration
- `GET /api/admin/audit-logs` — recent audit events

Every endpoint returns JSON errors with suitable HTTP status codes for authorization and validation failures.
