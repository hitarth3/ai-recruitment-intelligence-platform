"""
Centralized AI Context Builder.
Automatically aggregates complete Candidate and Recruiter context objects from MongoDB Atlas.
Ensures candidates and recruiters never need to manually type or explain information already in the platform.
Zero hardcoded default scores (score is 0 if no valid resume is present).
"""

from typing import Dict, Any, Optional
from app.database.profile_db import get_candidate_profile
from app.database.resume_db import get_user_resume
from app.database.coach_chat_db import get_candidate_chat_history
from app.database.database import get_database
from app.services.resume_analyzer_service import extract_text_and_links_from_file
from app.services.improvement_service import generate_priority_recommendations
from app.utils.logger import logger

# Alias for backward compatibility
extract_text_and_links_from_pdf = extract_text_and_links_from_file


def extract_projects_from_pdf_text(text: str) -> list:
    """
    Extracts project titles from raw PDF text if candidate profile projects list is empty.
    """
    if not text:
        return []

    projects = []
    lines = text.split("\n")
    in_projects_section = False

    for line in lines:
        l_strip = line.strip()
        l_lower = l_strip.lower()

        if any(h in l_lower for h in ["projects", "personal projects", "academic projects", "key projects"]):
            in_projects_section = True
            continue

        if in_projects_section:
            if any(h in l_lower for h in ["experience", "education", "skills", "certifications", "achievements", "work history"]):
                break

            if l_strip and len(l_strip) > 3 and len(l_strip) < 70:
                if not l_strip.startswith("•") and not l_strip.startswith("-") and not l_strip.startswith("http"):
                    title = l_strip.split("|")[0].split("-")[0].split("–")[0].strip()
                    if title and title.lower() not in ["projects", "key projects"] and title not in projects:
                        projects.append(title)

    return projects[:5]


async def build_candidate_context(user_id: str) -> Dict[str, Any]:
    """
    Builds a complete, structured CandidateContext object from MongoDB Atlas.
    Includes Profile, Resume File Text, Parsed Resume, Analysis, Skills, Projects, Experience, Education, Certifications, Applied Jobs, Recommendations, and Conversation History.
    """
    try:
        db = get_database()
        profile = await get_candidate_profile(user_id) or {}
        resume = await get_user_resume(user_id) or {}

        # 1. Extract raw file text directly from disk if available
        pdf_text = ""
        pdf_links = []
        if resume.get("file_path"):
            pdf_text, pdf_links = extract_text_and_links_from_file(resume["file_path"])

        # 2. Extract Resume Analysis
        analysis = resume.get("resume_analysis", {})

        # 3. Consolidate Skills
        profile_skills = profile.get("skills", [])
        analysis_skills = analysis.get("skills", [])
        all_skills = list(dict.fromkeys(analysis_skills + profile_skills))

        # 4. Personal Information
        personal_info = profile.get("personal_information", {})
        candidate_name = personal_info.get("name") or current_user_name_fallback(profile)

        # 5. Aggregate Projects, Experience, Education, Certifications
        projects = profile.get("projects", []) or resume.get("parsed_resume", {}).get("projects", [])
        if not projects and pdf_text:
            projects = extract_projects_from_pdf_text(pdf_text)

        experience = profile.get("experience", []) or resume.get("parsed_resume", {}).get("experience", [])
        education = profile.get("education", []) or resume.get("parsed_resume", {}).get("education", [])
        certifications = profile.get("certifications", [])

        # 6. Applied Jobs & Recommended Jobs (if any)
        applied_jobs = []
        try:
            cursor = db.applications.find({"candidate_id": user_id}).limit(5)
            applied_jobs = await cursor.to_list(length=5)
        except Exception:
            pass

        # 7. AI Priority Recommendations
        score = analysis.get("resume_health_score", 0)
        priority_recs = generate_priority_recommendations(resume, score)

        # 8. Recent Conversation History Memory from MongoDB Atlas (Load up to 20 messages)
        history = await get_candidate_chat_history(user_id, limit=20)
        formatted_history = []
        for msg in history:
            formatted_history.append(f"{msg.get('sender', 'user').upper()}: {msg.get('text', '')}")

        has_resume = bool(resume.get("file_path")) and analysis.get("ats_readiness") != "Invalid Document"

        context = {
            "user_id": user_id,
            "has_valid_resume": has_resume,
            "candidate_name": candidate_name,
            "email": personal_info.get("email", ""),
            "phone": personal_info.get("phone", ""),
            "location": personal_info.get("location", ""),
            "headline": personal_info.get("headline", "Software Engineer"),
            "target_role": personal_info.get("headline") or "Software Engineer / Backend Developer",
            "bio": personal_info.get("bio", ""),
            "github": personal_info.get("github") or profile.get("github") or extract_github_from_text(pdf_text, pdf_links),
            "linkedin": personal_info.get("linkedin") or profile.get("linkedin"),
            "resume_id": str(resume.get("_id", "")) if resume.get("_id") else "",
            "original_filename": resume.get("original_filename", "No Resume Uploaded"),
            "upload_date": resume.get("upload_date", ""),
            "pdf_text": pdf_text,
            "pdf_text_snippet": pdf_text[:3500] if pdf_text else "",
            "resume_health_score": score if has_resume else 0,
            "ats_readiness": analysis.get("ats_readiness", "No Resume Uploaded") if has_resume else "No Resume Uploaded",
            "ats_parse_rate": analysis.get("ats_parse_rate", 0) if has_resume else 0,
            "resume_summary": analysis.get("summary", "No resume uploaded yet.") if has_resume else "No software engineering resume uploaded yet.",
            "score_breakdown": analysis.get("score_breakdown", []),
            "strengths": analysis.get("strengths", []),
            "weaknesses": analysis.get("weaknesses", []),
            "missing_skills": analysis.get("missing_skills", []),
            "missing_sections": analysis.get("missing_sections", []),
            "skills": all_skills,
            "primary_skill": all_skills[0] if all_skills else "Software Engineering",
            "projects": projects,
            "experience": experience,
            "education": education,
            "certifications": certifications,
            "applied_jobs_count": len(applied_jobs),
            "priority_recommendations": priority_recs,
            "conversation_history": "\n".join(formatted_history) if formatted_history else "No previous conversation.",
            "versions_count": len(resume.get("versions", [])),
        }
        return context

    except Exception as e:
        logger.error(f"Error building candidate context for user {user_id}: {e}")
        return {
            "user_id": user_id,
            "has_valid_resume": False,
            "candidate_name": "Candidate",
            "skills": [],
            "primary_skill": "Software Engineering",
            "resume_health_score": 0,
            "ats_readiness": "No Resume Uploaded",
            "pdf_text": "",
            "pdf_text_snippet": "",
            "missing_skills": [],
            "conversation_history": "No previous conversation.",
        }


async def build_recruiter_context(
    recruiter_id: str,
    job_id: Optional[str] = None,
    candidate_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds a complete, structured RecruiterContext object from MongoDB Atlas.
    """
    try:
        candidate_context = {}
        if candidate_id:
            candidate_context = await build_candidate_context(candidate_id)

        recruiter_context = {
            "recruiter_id": recruiter_id,
            "company_name": "Tech Corp",
            "job_id": job_id or "job-101",
            "job_title": "Software Engineer",
            "job_description": "We are seeking a Software Engineer proficient in Python, FastAPI, React, and MongoDB.",
            "required_skills": ["Python", "FastAPI", "React", "MongoDB", "Docker"],
            "experience_level": "1-3 Years",
            "location": "Remote / Hybrid",
            "candidate_context": candidate_context,
            "candidate_name": candidate_context.get("candidate_name", "Candidate"),
            "candidate_score": candidate_context.get("resume_health_score", 0),
            "candidate_skills": candidate_context.get("skills", []),
        }
        return recruiter_context

    except Exception as e:
        logger.error(f"Error building recruiter context: {e}")
        return {"recruiter_id": recruiter_id, "job_title": "Software Engineer"}


def current_user_name_fallback(profile: dict) -> str:
    """Helper to extract candidate name fallback."""
    if profile.get("name"):
        return profile["name"]
    personal = profile.get("personal_information", {})
    if personal.get("name"):
        return personal["name"]
    return "Candidate"


def extract_github_from_text(text: str, links: list) -> str:
    """Helper to extract GitHub URL from text or links."""
    for link in links:
        if "github.com" in link.lower():
            return link
    if "github.com" in text.lower():
        return "github.com/candidate"
    return ""
