"""
AI Recruiter Interview Question Generator Module.
Uses RecruiterContext and GeminiService to generate candidate-specific technical screening questions.
"""

from typing import Dict, Any, List
from app.ai.gemini_service import gemini_service
from app.ai.context_builder import build_recruiter_context
from app.ai.prompt_builder import build_recruiter_interview_questions_prompt
from app.utils.logger import logger


async def generate_interview_questions_pipeline(recruiter_id: str, job_id: str, candidate_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates tailored technical interview screening questions for recruiters.
    """
    recruiter_context = await build_recruiter_context(recruiter_id, job_id, candidate_id)
    
    if gemini_service.is_configured:
        prompt = build_recruiter_interview_questions_prompt(recruiter_context)
        ai_reply = gemini_service.generate_text(prompt)
        if ai_reply:
            return {"questions_text": ai_reply, "context": recruiter_context}

    # Fallback Dynamic Generator
    skills = recruiter_context.get("candidate_skills", ["Python", "FastAPI", "React"])
    job_title = recruiter_context.get("job_title", "Software Engineer")
    candidate_name = recruiter_context.get("candidate_name", "Candidate")

    questions = [
        f"1. **{skills[0] if skills else 'System'} Performance**: How have you used {skills[0] if skills else 'Python'} to optimize API latency and database query execution?",
        f"2. **API Architecture**: Describe your experience designing RESTful APIs with {skills[1] if len(skills)>1 else 'FastAPI'}. How do you handle error states and JWT authentication?",
        f"3. **Database Scaling**: Walk us through compound indexing and schema optimization in MongoDB or SQL.",
        f"4. **Deployment & DevOps**: How do you containerize web microservices using Docker for production staging?",
        f"5. **System Reliability**: Describe a technical issue you encountered in your projects and how you resolved it."
    ]

    return {
        "candidate_name": candidate_name,
        "job_title": job_title,
        "questions": questions,
        "context": recruiter_context
    }
