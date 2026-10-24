import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from uuid import uuid4

from app.repositories.resume_repository import ResumeRepository


class ResumeService:
    ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}

    def __init__(self, upload_folder="app/uploads/resumes", repo=None):
        self.upload_folder = upload_folder
        self.repo = repo or ResumeRepository()
        os.makedirs(self.upload_folder, exist_ok=True)

    def save_resume(self, file, candidate_id):
        if not file or file.filename == "":
            raise ValueError("No resume file selected.")
        original_name = secure_filename(file.filename)
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Resume must be a PDF, DOC, or DOCX file.")
        filename = f"{uuid4().hex}{ext}"
        path = os.path.join(self.upload_folder, filename)
        file.save(path)
        try:
            resume = self.repo.insert_one({
                "candidate_id": candidate_id,
                "filename": filename,
                "original_name": original_name,
                "storage_path": path,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            os.remove(path)
            raise
        return resume

    def list_for_candidate(self, candidate_id):
        return self.repo.for_candidate(candidate_id)

    def find_resume(self, resume_id):
        return self.repo.find_by_id(resume_id)

    def delete_resume(self, resume_id):
        resume = self.repo.delete_one(resume_id)
        if resume and os.path.isfile(resume["storage_path"]):
            os.remove(resume["storage_path"])
        return resume
