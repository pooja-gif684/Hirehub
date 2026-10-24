# HireHub MongoDB Data Model

The application connects to the database selected by `MONGO_DBNAME` (defaults to `hirehub`) using `MONGO_URI`.

## Collections

- `users`: candidate, recruiter, and admin accounts, including candidate profile fields and password hashes
- `companies`: recruiter-owned company profiles, uniquely associated with one recruiter
- `jobs`: recruiter job postings and search fields
- `applications`: candidate applications, status, and cover letter
- `interviews`: scheduled interviews and meeting details
- `notifications`: per-user application and interview updates
- `resumes`: uploaded resume metadata and local storage paths
- `audit_logs`: actor, action, resource, timestamp, and request IP

Dashboard analytics and reports are calculated from these collections. MongoDB indexes enforce unique user email addresses, record IDs, one company profile per recruiter, and one application per candidate/job pair.

Resume file contents are saved under `UPLOAD_FOLDER`; they are not stored as MongoDB documents.
