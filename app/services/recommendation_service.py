class RecommendationService:
    def __init__(self, job_service=None):
        self.job_service = job_service

    def recommend_for_candidate(self, candidate):
        jobs = self.job_service.list_jobs() if self.job_service else []
        candidate_skills = {
            skill.strip().lower()
            for skill in candidate.get("skills", [])
            if isinstance(skill, str) and skill.strip()
        }
        recommendations = []

        for job in jobs:
            requirements = job.get("requirements", [])
            if not isinstance(requirements, list):
                requirements = []
            text = " ".join([
                str(job.get("title", "")),
                str(job.get("description", "")),
                " ".join(str(requirement) for requirement in requirements),
                str(job.get("category", "")),
            ])
            job_terms = {term.strip(".,;:()[]{}").lower() for term in text.split()}
            score = len(candidate_skills & job_terms)
            if score:
                recommendations.append({**job, "match_score": score})

        return sorted(recommendations, key=lambda item: item["match_score"], reverse=True)
