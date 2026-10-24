# HireHub

HireHub is a full-featured recruitment and hiring portal built with Flask, MongoDB, Bootstrap 5, and Jinja2. It supports candidate, recruiter, and admin workflows, including authentication, job management, applications, resume handling, dashboards, and APIs.

## Features

- Role-based access for candidate, recruiter, and admin
- User registration, login, logout, and session management
- Werkzeug password hashing, password changes, and role-based access control
- HTTP-only, SameSite session cookies with configurable Secure cookies and expiry
- Candidate and recruiter profile management
- Recruiter company profiles with recruiter-scoped editing
- Recruiter job creation, editing, closing, deleting, searching, and filtering
- Candidate applications, duplicate prevention, and status tracking
- Resume upload, secure download, and recruiter access for applicants
- Interview scheduling, interview tracking, and candidate notifications
- Candidate job recommendations matched against profile skills
- Admin user/job/application management, audit logs, reports, and analytics
- Role-protected REST APIs across authentication, profiles, jobs, applications, resumes, interviews, notifications, reports, and administration
- Responsive Bootstrap 5 UI

## Tech Stack

- Backend: Python 3.12+, Flask, PyMongo, Jinja2, Werkzeug
- Frontend: HTML5, CSS3, Bootstrap 5, JavaScript
- Database: MongoDB
- Testing: pytest

## MongoDB

Users and profiles, jobs, applications, interviews, notifications, resume metadata, and audit events are stored in MongoDB. The configured database name defaults to `hirehub`; the app creates the required unique indexes at startup. It reports a connection error if MongoDB is unavailable. Resume file contents remain in the local `UPLOAD_FOLDER`.

Set `MONGO_URI` and `MONGO_DBNAME` in `.env` to use a different MongoDB deployment or database. Do not use the development MongoDB connection or default credentials in production.

## Project Structure

```text
hirehub/
├── run.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   ├── routes/
│   │   ├── api/
│   │   └── web/
│   ├── repositories/
│   ├── services/
│   ├── templates/
│   ├── static/
│   ├── uploads/
│   └── utils/
├── scripts/
├── docs/
└── tests/
```

## Setup and Run

Run these commands in PowerShell from the project folder (`C:\Users\HP\Hirehub`). Copy only the commands inside the code block; do not type headings such as “Windows PowerShell:” or the `PS C:\...>` prompt.

Start a local MongoDB server first. By default, HireHub connects to `mongodb://localhost:27017` and stores application data in the `hirehub` database. MongoDB must be running before you start the Flask app.

```powershell
python -m venv .venv
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

The execution policy change applies only to the current PowerShell window. If your organization manages the policy and PowerShell still blocks activation, skip activation and run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

For Windows Command Prompt, activate with:

```cmd
.venv\Scripts\activate.bat
```

For macOS/Linux, use:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

Once the server starts, open this address in your browser:

```text
http://localhost:5000
```

## Default Admin Login

On first startup, HireHub creates a development administrator account if one does not already exist:

- Email: `admin@hirehub.local`
- Password: `HireHubDev@2026!`

Sign in at `http://localhost:5000/login`, then open the Admin Dashboard. You can override these values in `.env` using `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD`. The password is hashed before it is stored. This default is for local development only; set a unique password before using the app in any shared or production environment.

## Environment Variables

Create a `.env` file using `.env.example` and update values as needed:

```env
SECRET_KEY=hirehub-dev-secret
FLASK_ENV=development
MONGO_URI=mongodb://localhost:27017/hirehub
MONGO_DBNAME=hirehub
MONGO_TIMEOUT_MS=5000
UPLOAD_FOLDER=app/uploads/resumes
DEFAULT_ADMIN_EMAIL=admin@hirehub.local
DEFAULT_ADMIN_PASSWORD=HireHubDev@2026!
SESSION_COOKIE_SECURE=false
FLASK_DEBUG=false
```

## Notes

This project uses a modular Flask architecture with blueprints, MongoDB-backed repositories, and services to keep the application organized and maintainable. Local development uses the default admin account below. Change its password and set a private `SECRET_KEY` before exposing the app outside a trusted local environment. Set `SESSION_COOKIE_SECURE=true` when serving over HTTPS.
