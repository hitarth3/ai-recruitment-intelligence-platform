"""
FastAPI REST Router for Job Posting & Management.
Implements candidate job discovery (GET /), published job count (GET /count), recruiter management (POST /, GET /my-jobs, GET /dashboard-stats, GET /{id}, PUT /{id}, PATCH /{id}/status, DELETE /{id}).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header, Body
from typing import Dict, Any, List, Optional
from app.api.v1.auth.dependencies import get_current_recruiter, get_current_user
from app.core.security import decode_access_token
from app.schemas.job import (
    JobCreateRequest,
    JobUpdateRequest,
    JobStatusPatchRequest,
    JobResponse
)
from app.database.company_db import get_company_by_recruiter_id, create_company_profile
from app.database.job_db import (
    create_job,
    get_job_by_id,
    get_my_company_jobs,
    get_published_jobs,
    get_published_jobs_count,
    update_job,
    patch_job_status,
    delete_job,
    get_dashboard_stats,
    get_job_workflow,
    update_job_workflow
)
from app.utils.logger import logger

job_router = APIRouter(prefix="/jobs", tags=["Job Management"])


def extract_optional_candidate_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optional Bearer token extractor to identify candidate user ID if available.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if payload and payload.get("role") == "candidate":
        return payload.get("sub")
    return None


@job_router.get("", response_model=Dict[str, Any])
@job_router.get("/", response_model=Dict[str, Any])
async def discover_published_jobs(
    tab: Optional[str] = Query("all", description="Tab selection: 'recommended' or 'all'"),
    search: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("newest"),
    authorization: Optional[str] = Header(None)
):
    """
    Unified Candidate Job Discovery Endpoint:
    Fetches Published jobs from MongoDB Atlas with tab filtering ('recommended' or 'all').
    Computes candidate skill match percentage and breakdown.
    Supports search, multi-filter, and sorting (newest, oldest, highest_salary, lowest_salary, recently_updated).
    """
    candidate_id = extract_optional_candidate_id(authorization)
    jobs, total_published, recommended_count = await get_published_jobs(
        tab=tab or "all",
        search=search,
        employment_type=employment_type,
        work_mode=work_mode,
        category=category,
        sort_by=sort_by,
        candidate_id=candidate_id
    )
    return {
        "jobs": jobs,
        "total": len(jobs),
        "total_published": total_published,
        "recommended_count": recommended_count
    }


@job_router.get("/count", response_model=Dict[str, Any])
async def get_published_count(authorization: Optional[str] = Header(None)):
    """
    Lightweight endpoint returning total_published and recommended_count of Published jobs in MongoDB Atlas.
    """
    candidate_id = extract_optional_candidate_id(authorization)
    counts = await get_published_jobs_count(candidate_id=candidate_id)
    return counts


@job_router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@job_router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def post_new_job(
    payload: Dict[str, Any] = Body(...),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Creates a new Job Requisition in MongoDB Atlas using 7-step wizard data.
    Automatically attaches recruiter's company_id, company_name, and company_logo.
    """
    try:
        recruiter_id = str(current_recruiter.get("_id") or current_recruiter.get("id"))
        logger.info(f"[JobPosting API] Incoming post_new_job request from Recruiter ID {recruiter_id}")
        logger.info(f"[JobPosting API] Payload: {payload}")

        if not recruiter_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid recruiter credentials.")

        company = await get_company_by_recruiter_id(recruiter_id)
        if not company:
            recruiter_name = current_recruiter.get("full_name") or current_recruiter.get("email", "Recruiter").split("@")[0]
            comp_name = current_recruiter.get("company_name") or f"{recruiter_name}'s Organization"
            company = await create_company_profile(recruiter_id, {
                "company_name": comp_name,
                "industry": "Technology",
                "company_size": "10-50",
                "description": "Tech hiring organization."
            })
            logger.info(f"[JobPosting API] Created default company profile '{comp_name}' for recruiter {recruiter_id}")

        company_id = company.get("id") or str(company.get("_id", ""))
        comp_name = company.get("company_name", "Organization")
        comp_logo = company.get("company_logo", "")

        logger.info(f"[JobPosting API] Recruiter {recruiter_id} bound to Company '{comp_name}' [{company_id}]")

        new_job = await create_job(
            recruiter_id=recruiter_id,
            company_id=company_id,
            company_name=comp_name,
            company_logo=comp_logo,
            job_payload=payload
        )

        job_id = new_job.get("id")
        logger.info(f"[JobPosting API] Successfully created Job Requisition in MongoDB Atlas: Job ID '{job_id}'")

        # Verify immediate database lookup
        verification = await get_job_by_id(job_id)
        if not verification:
            logger.error(f"[JobPosting API] CRITICAL: Job ID {job_id} inserted but lookup failed!")
            raise HTTPException(status_code=500, detail="Database insertion verification failed.")

        return {
            "success": True,
            "message": "Job requisition published successfully.",
            "id": job_id,
            **new_job
        }

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"[JobPosting API] Unexpected error creating job: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post job requisition: {str(err)}"
        )


@job_router.get("/my-jobs", response_model=Dict[str, Any])
async def list_my_company_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Fetches all jobs for the recruiter's company or recruiter user ID.
    Supports filtering by status (All | Draft | Published | Closed | Archived) and search query.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    jobs = await get_my_company_jobs(company_id=company_id, recruiter_id=recruiter_id, status_filter=status_filter, search_query=search)
    return {
        "jobs": jobs,
        "total": len(jobs),
        "company_name": company.get("company_name", "Company") if company else "Company"
    }


@job_router.get("/dashboard-stats", response_model=Dict[str, Any])
async def get_recruiter_dashboard_stats(current_recruiter: dict = Depends(get_current_recruiter)):
    """
    Fetches real aggregated MongoDB metrics for the Recruiter Dashboard.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    company_id = company["id"] if company else ""

    stats = await get_dashboard_stats(company_id=company_id, recruiter_id=recruiter_id)
    stats["company"] = company
    return stats


@job_router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_detail(
    job_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Fetches single job requisition detail.
    """
    candidate_id = extract_optional_candidate_id(authorization)
    job = await get_job_by_id(job_id, candidate_id=candidate_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requisition not found."
        )
    return job


@job_router.put("/{job_id}", response_model=Dict[str, Any])
async def update_job_requisition(
    job_id: str,
    payload: JobUpdateRequest,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Updates an existing job requisition.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized company action."
        )

    update_data = payload.model_dump(exclude_unset=True)
    updated = await update_job(job_id, company["id"], update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requisition not found or unauthorized."
        )
    return updated


@job_router.patch("/{job_id}/status", response_model=Dict[str, Any])
async def change_job_status(
    job_id: str,
    payload: JobStatusPatchRequest,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Updates status of job requisition (Draft | Published | Closed | Archived).
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized company action."
        )

    updated = await patch_job_status(job_id, company["id"], payload.status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requisition not found or unauthorized."
        )
    return updated


@job_router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job_requisition(
    job_id: str,
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Deletes job requisition document.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized company action."
        )

    deleted = await delete_job(job_id, company["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requisition not found or already deleted."
        )
    return {"message": "Job requisition deleted successfully."}


@job_router.get("/{job_id}/workflow", response_model=Dict[str, Any])
async def get_job_hiring_workflow(job_id: str):
    """
    Retrieves configured hiring workflow stages for a job requisition.
    """
    stages = await get_job_workflow(job_id)
    return {"job_id": job_id, "workflow": stages}


@job_router.put("/{job_id}/workflow", response_model=Dict[str, Any])
async def save_job_hiring_workflow(
    job_id: str,
    payload: Dict[str, Any] = Body(...),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    """
    Saves custom hiring workflow stages for a job requisition configured via Workflow Builder Page.
    """
    recruiter_id = str(current_recruiter["_id"])
    company = await get_company_by_recruiter_id(recruiter_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized company action."
        )

    workflow_stages = payload.get("workflow") or payload.get("stages") or []
    if not isinstance(workflow_stages, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow stages must be a valid array of stage objects."
        )

    updated_stages = await update_job_workflow(job_id, company["id"], workflow_stages)
    return {"message": "Hiring workflow saved successfully.", "job_id": job_id, "workflow": updated_stages}
