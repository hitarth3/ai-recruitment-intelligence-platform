"""
MongoDB Atlas Job Collection Handler.
Manages 7-step Job Requisition CRUD, unified Candidate Job Discovery (Recommended & All Jobs),
skill match computation, status toggling, and recruiter dashboard stats aggregation.
Automatically attaches company_id, recruiter_id, company_name, and company_logo.
Converts BSON ObjectId to string for 100% clean FastAPI JSON serialization.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId
from app.database.database import get_database
from app.utils.logger import logger


def calculate_skill_match(job_skills: Dict[str, Any], candidate_skills: List[str]) -> Dict[str, Any]:
    """
    Computes candidate skill match percentage and breakdown against job required skills.
    Returns match_percentage, matched_skills list, and missing_skills list.
    """
    required = job_skills.get("required_skills", []) or []
    if not required:
        # Fallback if no required skills explicitly declared
        return {
            "match_percentage": 85,
            "matched_skills": candidate_skills[:3] if candidate_skills else ["General Technical Skills"],
            "missing_skills": []
        }

    cand_set = set(s.strip().lower() for s in candidate_skills if isinstance(s, str))
    matched = []
    missing = []

    for req_skill in required:
        if req_skill.strip().lower() in cand_set:
            matched.append(req_skill)
        else:
            missing.append(req_skill)

    total_req = len(required)
    match_ratio = len(matched) / total_req
    
    # Calculate percentage (min 50% baseline if candidate has skills, max 98%)
    if len(matched) == total_req:
        pct = 96
    elif len(matched) > 0:
        pct = max(60, min(92, round(50 + (match_ratio * 45))))
    else:
        pct = 50

    return {
        "match_percentage": pct,
        "matched_skills": matched,
        "missing_skills": missing
    }


def build_default_workflow_stages() -> List[Dict[str, Any]]:
    return [
        {
            "stage_id": "stage-ai-screening",
            "stage_name": "AI Resume Screening",
            "stage_type": "AI",
            "display_order": 1,
            "enabled": True,
            "configuration": {
                "auto_execute": True,
                "auto_advance": True,
                "auto_reject": True,
                "minimum_match_score": 75,
                "auto_shortlist_threshold": 85,
                "auto_reject_threshold": 45,
                "recruiter_approval_required": False
            }
        },
        {
            "stage_id": "stage-tech-assessment",
            "stage_name": "Technical Assessment",
            "stage_type": "AI",
            "display_order": 2,
            "enabled": True,
            "configuration": {
                "assessment_type": "coding",
                "duration_minutes": 60,
                "auto_advance": True,
                "auto_reject": True,
                "passing_score": 70,
                "max_attempts": 1,
                "programming_languages": ["TypeScript", "Python"],
                "recruiter_approval_required": False
            }
        },
        {
            "stage_id": "stage-ai-interview",
            "stage_name": "AI Interview",
            "stage_type": "AI",
            "display_order": 3,
            "enabled": True,
            "configuration": {
                "interview_duration_minutes": 30,
                "auto_advance": True,
                "auto_reject": True,
                "minimum_interview_score": 80,
                "communication_weight": 0.3,
                "technical_weight": 0.5,
                "confidence_weight": 0.2,
                "recruiter_approval_required": False
            }
        },
        {
            "stage_id": "stage-tech-interview",
            "stage_name": "Technical Interview",
            "stage_type": "Manual",
            "display_order": 4,
            "enabled": True,
            "configuration": {
                "interview_duration_minutes": 45,
                "required_feedback_form": True,
                "auto_advance": False,
                "auto_reject": False,
                "recruiter_approval_required": True
            }
        },
        {
            "stage_id": "stage-hr-interview",
            "stage_name": "HR Interview",
            "stage_type": "Manual",
            "display_order": 5,
            "enabled": True,
            "configuration": {
                "interview_duration_minutes": 30,
                "auto_advance": False,
                "auto_reject": False,
                "recruiter_approval_required": True
            }
        },
        {
            "stage_id": "stage-offer",
            "stage_name": "Offer",
            "stage_type": "Manual",
            "display_order": 6,
            "enabled": True,
            "configuration": {
                "auto_advance": False,
                "auto_reject": False,
                "recruiter_approval_required": True
            }
        }
    ]


async def create_job(
    recruiter_id: str,
    company_id: str,
    company_name: str,
    company_logo: str,
    job_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Creates a new Job Requisition document in db.jobs.
    Automatically attaches company_id, recruiter_id, company_name, company_logo,
    and structured hiring_workflow array.
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    hiring_wf = job_payload.get("hiring_workflow")
    if not hiring_wf or not isinstance(hiring_wf, list):
        hiring_wf = build_default_workflow_stages()

    title_val = str(job_payload.get("title") or "Software Engineer Requisition").strip()
    dept_val = str(job_payload.get("department") or "Engineering").strip()
    cat_val = str(job_payload.get("category") or "Fullstack Development").strip()
    desc_val = str(job_payload.get("description") or "Detailed job description requisition for software engineering position.").strip()

    doc = {
        "company_id": company_id,
        "recruiter_id": recruiter_id,
        "company_name": company_name or "Organization",
        "company_logo": company_logo or "",
        "title": title_val,
        "department": dept_val,
        "category": cat_val,
        "employment_type": job_payload.get("employment_type", "Full-time"),
        "open_positions": job_payload.get("open_positions", 1),
        "location": job_payload.get("location") if isinstance(job_payload.get("location"), dict) else {},
        "experience": job_payload.get("experience") if isinstance(job_payload.get("experience"), dict) else {},
        "salary": job_payload.get("salary") if isinstance(job_payload.get("salary"), dict) else {},
        "education": job_payload.get("education") if isinstance(job_payload.get("education"), dict) else {},
        "skills": job_payload.get("skills") if isinstance(job_payload.get("skills"), dict) else {},
        "description": desc_val,
        "responsibilities": job_payload.get("responsibilities", []),
        "requirements": job_payload.get("requirements", []),
        "benefits": job_payload.get("benefits", []),
        "settings": job_payload.get("settings") if isinstance(job_payload.get("settings"), dict) else {},
        "hiring_workflow": hiring_wf,
        "status": job_payload.get("status", "Published"),  # Draft | Published | Closed | Archived
        "applications_count": 0,
        "views_count": 0,
        "created_at": now,
        "updated_at": now
    }

    result = await db["jobs"].insert_one(doc)
    job_id = str(result.inserted_id)
    doc["id"] = job_id
    doc["_id"] = job_id

    logger.info(f"Created Job Requisition: '{doc['title']}' [{doc['status']}] for Company ID {company_id}")
    return doc


async def get_job_by_id(job_id: str, candidate_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches single job requisition by ObjectId string.
    Checks if candidate has already applied if candidate_id is provided.
    """
    try:
        db = get_database()
        try:
            job = await db["jobs"].find_one({"_id": ObjectId(job_id)})
        except Exception:
            job = await db["jobs"].find_one({"_id": job_id})

        if job:
            job["id"] = str(job["_id"])
            job["_id"] = str(job["_id"])
            
            if candidate_id:
                try:
                    applied_doc = await db["applications"].find_one({"candidate_id": candidate_id, "job_id": job["id"]})
                    job["has_applied"] = applied_doc is not None

                    # Compute candidate match metrics
                    resume = await db["resumes"].find_one({"user_id": candidate_id})
                    cand_skills = resume.get("skills", []) if resume else []
                    match_info = calculate_skill_match(job.get("skills", {}), cand_skills)
                    job.update(match_info)
                except Exception:
                    job["has_applied"] = False
            else:
                job["has_applied"] = False
        return job
    except Exception as err:
        logger.error(f"Error finding job ID {job_id}: {err}")
        return None


async def get_my_company_jobs(
    company_id: str,
    recruiter_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches all jobs for a company or recruiter with optional status filtering (Draft/Published/Closed/Archived)
    and title search.
    """
    db = get_database()
    
    match_conditions = []
    if company_id:
        match_conditions.append({"company_id": company_id})
    if recruiter_id:
        match_conditions.append({"recruiter_id": recruiter_id})

    query: Dict[str, Any] = {}
    if len(match_conditions) > 1:
        query = {"$or": match_conditions}
    elif len(match_conditions) == 1:
        query = match_conditions[0]

    if status_filter and status_filter.lower() != "all":
        query["status"] = {"$regex": f"^{status_filter}$", "$options": "i"}

    if search_query and search_query.strip():
        regex = {"$regex": search_query.strip(), "$options": "i"}
        search_or = [
            {"title": regex},
            {"department": regex},
            {"category": regex}
        ]
        if "$or" in query:
            query = {"$and": [query, {"$or": search_or}]}
        else:
            query["$or"] = search_or

    cursor = db["jobs"].find(query).sort("created_at", -1)
    jobs = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc["_id"] = str(doc["_id"])
        jobs.append(doc)
    return jobs


async def get_published_jobs(
    tab: str = "all",  # "recommended" | "all"
    search: Optional[str] = None,
    employment_type: Optional[str] = None,
    work_mode: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = "newest",
    candidate_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Unified Published Jobs discovery handler for Candidates.
    Returns (jobs_list, total_published_count, recommended_count).
    - If tab == 'recommended': returns published unapplied jobs sorted by candidate skill match %.
    - If tab == 'all': returns all published jobs in MongoDB Atlas, marking has_applied boolean.
    Never returns Draft, Closed, or Archived jobs.
    """
    db = get_database()
    query: Dict[str, Any] = {"status": {"$regex": "^Published$", "$options": "i"}}

    if search and search.strip():
        regex = {"$regex": search.strip(), "$options": "i"}
        query["$or"] = [
            {"title": regex},
            {"company_name": regex},
            {"department": regex},
            {"category": regex},
            {"location.city": regex},
            {"skills.required_skills": regex}
        ]

    if employment_type and employment_type.lower() != "all":
        query["employment_type"] = {"$regex": f"^{employment_type}$", "$options": "i"}

    if work_mode and work_mode.lower() != "all":
        query["location.work_mode"] = {"$regex": f"^{work_mode}$", "$options": "i"}

    if category and category.lower() != "all":
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}

    # Determine Sorting criteria
    sort_spec = [("created_at", -1)]
    if sort_by == "oldest":
        sort_spec = [("created_at", 1)]
    elif sort_by == "highest_salary":
        sort_spec = [("salary.max_salary", -1)]
    elif sort_by == "lowest_salary":
        sort_spec = [("salary.min_salary", 1)]
    elif sort_by == "recently_updated":
        sort_spec = [("updated_at", -1)]

    cursor = db["jobs"].find(query).sort(sort_spec)

    # Candidate Application and Resume Skills Context
    applied_job_ids = set()
    candidate_skills = []
    if candidate_id:
        try:
            apps_cursor = db["applications"].find({"candidate_id": candidate_id}, {"job_id": 1})
            async for app_doc in apps_cursor:
                applied_job_ids.add(app_doc["job_id"])

            resume = await db["resumes"].find_one({"user_id": candidate_id})
            if resume and "skills" in resume:
                candidate_skills = resume["skills"]
        except Exception as err:
            logger.error(f"Error fetching candidate context: {err}")

    # Fetch all matching published jobs
    all_published_jobs = []
    recommended_jobs = []

    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc["_id"] = str(doc["_id"])
        
        has_applied = doc["id"] in applied_job_ids
        doc["has_applied"] = has_applied

        # Compute skill match info
        match_info = calculate_skill_match(doc.get("skills", {}), candidate_skills)
        doc.update(match_info)

        all_published_jobs.append(doc)

        # Recommended Tab excludes jobs candidate has already applied to
        if not has_applied:
            recommended_jobs.append(doc)

    # Sort recommended jobs by match_percentage desc by default
    recommended_jobs.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)

    total_published_count = len(all_published_jobs)
    recommended_count = len(recommended_jobs)

    target_jobs = recommended_jobs if tab.lower() == "recommended" else all_published_jobs
    return target_jobs, total_published_count, recommended_count


async def get_published_jobs_count(candidate_id: Optional[str] = None) -> Dict[str, int]:
    """
    Lightweight count endpoint returning total_published and recommended_count.
    """
    db = get_database()
    total_published = await db["jobs"].count_documents({"status": "Published"})

    recommended_count = total_published
    if candidate_id:
        try:
            apps_count = await db["applications"].count_documents({"candidate_id": candidate_id})
            recommended_count = max(0, total_published - apps_count)
        except Exception:
            pass

    return {
        "total_published": total_published,
        "recommended_count": recommended_count
    }


async def update_job(
    job_id: str,
    company_id: str,
    update_payload: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Updates an existing job requisition for a recruiter's company.
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    clean_data = {k: v for k, v in update_payload.items() if v is not None}
    clean_data["updated_at"] = now

    result = await db["jobs"].update_one(
        {"_id": ObjectId(job_id), "company_id": company_id},
        {"$set": clean_data}
    )

    if result.modified_count > 0 or result.matched_count > 0:
        return await get_job_by_id(job_id)
    return None


async def patch_job_status(
    job_id: str,
    company_id: str,
    new_status: str
) -> Optional[Dict[str, Any]]:
    """
    Updates status of job requisition (Draft | Published | Closed | Archived).
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    valid_statuses = ["Draft", "Published", "Closed", "Archived"]
    normalized_status = new_status.capitalize()
    if normalized_status not in valid_statuses:
        normalized_status = "Published"

    await db["jobs"].update_one(
        {"_id": ObjectId(job_id), "company_id": company_id},
        {"$set": {"status": normalized_status, "updated_at": now}}
    )

    logger.info(f"Updated status of Job {job_id} to '{normalized_status}'")
    return await get_job_by_id(job_id)


async def delete_job(job_id: str, company_id: str) -> bool:
    """
    Deletes job requisition document.
    """
    db = get_database()
    result = await db["jobs"].delete_one({"_id": ObjectId(job_id), "company_id": company_id})
    return result.deleted_count > 0


async def get_dashboard_stats(company_id: str, recruiter_id: str = "") -> Dict[str, Any]:
    """
    Aggregates real statistics from MongoDB Atlas for the Recruiter Dashboard.
    Queries by company_id if available, falls back to recruiter_id if company_id is missing.
    Uses $or query to match both company_id and recruiter_id for maximum coverage.
    """
    db = get_database()

    # Build flexible query — match by company_id OR recruiter_id
    if company_id and recruiter_id:
        job_query = {"$or": [{"company_id": company_id}, {"recruiter_id": recruiter_id}]}
        app_query = {"$or": [{"company_id": company_id}, {"recruiter_id": recruiter_id}]}
    elif company_id:
        job_query = {"company_id": company_id}
        app_query = {"company_id": company_id}
    elif recruiter_id:
        job_query = {"recruiter_id": recruiter_id}
        app_query = {"recruiter_id": recruiter_id}
    else:
        return {
            "total_jobs": 0,
            "published_jobs": 0,
            "draft_jobs": 0,
            "closed_jobs": 0,
            "archived_jobs": 0,
            "applications_received": 0,
            "interviews_scheduled": 0
        }

    def with_status(base_query: dict, status: str) -> dict:
        """Safely combine an $or base query with a status filter using $and."""
        if "$or" in base_query:
            return {"$and": [base_query, {"status": status}]}
        return {**base_query, "status": status}

    total_jobs = await db["jobs"].count_documents(job_query)
    published_jobs = await db["jobs"].count_documents(with_status(job_query, "Published"))
    draft_jobs = await db["jobs"].count_documents(with_status(job_query, "Draft"))
    closed_jobs = await db["jobs"].count_documents(with_status(job_query, "Closed"))
    archived_jobs = await db["jobs"].count_documents(with_status(job_query, "Archived"))
    applications_received = await db["applications"].count_documents(app_query)
    interviews_scheduled = await db["applications"].count_documents(with_status(app_query, "Interview"))

    return {
        "total_jobs": total_jobs,
        "published_jobs": published_jobs,
        "draft_jobs": draft_jobs,
        "closed_jobs": closed_jobs,
        "archived_jobs": archived_jobs,
        "applications_received": applications_received,
        "interviews_scheduled": interviews_scheduled
    }


async def get_job_workflow(job_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves configured hiring workflow stages for a job requisition.
    Returns default stages if no custom workflow has been saved yet.
    """
    job = await get_job_by_id(job_id)
    if not job:
        return build_default_workflow_stages()

    workflow = job.get("hiring_workflow")
    if not workflow or not isinstance(workflow, list) or len(workflow) == 0:
        return build_default_workflow_stages()

    return workflow


async def update_job_workflow(job_id: str, company_id: str, workflow_stages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Updates the custom hiring workflow stages for a job requisition.
    Ensures stage_id, stage_name, stage_type, display_order, enabled, and configuration are preserved.
    """
    now = datetime.now(timezone.utc)
    db = get_database()

    try:
        query = {"_id": ObjectId(job_id), "company_id": company_id}
    except Exception:
        query = {"_id": job_id, "company_id": company_id}

    await db["jobs"].update_one(
        query,
        {"$set": {"hiring_workflow": workflow_stages, "updated_at": now}}
    )

    logger.info(f"Updated Hiring Workflow for Job {job_id} with {len(workflow_stages)} stages.")
    return workflow_stages
