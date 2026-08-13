"""
Automated Verification Test Suite for Phase 3 - Candidate Job Discovery & Application System:
1. Verify Candidate Job Discovery API (GET /api/v1/jobs) returns Published jobs.
2. Verify Candidate Application Creation (POST /api/v1/applications).
3. Verify MongoDB Atlas Application Persistence & Resume Version Attachment.
4. Verify Job applications_count increment & in-app notification generation.
5. Verify Duplicate Application Rejection.
6. Verify Candidate Applied Jobs Listing (GET /api/v1/applications/me).
7. Verify Application Withdrawal & Job applications_count decrement.
"""

import asyncio
from datetime import datetime, timezone
from passlib.context import CryptContext
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.database.company_db import create_company_profile
from app.database.job_db import create_job, get_published_jobs, get_job_by_id
from app.database.application_db import create_application, get_candidate_applications, withdraw_application

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def test_phase3_candidate_applications():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("RUNNING PHASE 3 - CANDIDATE APPLICATIONS TEST SUITE")
    print("==========================================================\n")

    # 1. Setup Recruiter & Published Job
    print("1. Setting up Recruiter, Company & Published Job Requisition...")
    await db["users"].delete_many({"email": "recruiter.phase3@example.com"})
    recruiter_doc = {
        "name": "Phase 3 Recruiter",
        "email": "recruiter.phase3@example.com",
        "password_hash": pwd_context.hash("Password123!"),
        "role": "recruiter",
        "email_verified": True,
        "profile_completed": True
    }
    recruiter_res = await db["users"].insert_one(recruiter_doc)
    recruiter_id = str(recruiter_res.inserted_id)

    company = await create_company_profile(recruiter_id, {
        "company_name": "Apex AI Corp",
        "industry": "Artificial Intelligence",
        "company_size": "50-200",
        "description": "Building state of the art AI platforms."
    })
    company_id = company["id"]

    job = await create_job(
        recruiter_id=recruiter_id,
        company_id=company_id,
        company_name=company["company_name"],
        company_logo="",
        job_payload={
            "title": "Senior AI Backend Engineer",
            "department": "Engineering",
            "category": "Data & AI",
            "employment_type": "Full-time",
            "open_positions": 1,
            "location": {"city": "San Francisco", "country": "USA", "work_mode": "Remote"},
            "experience": {"min_years": 3, "max_years": 6},
            "salary": {"min_salary": 150000, "max_salary": 190000, "currency": "USD"},
            "skills": {"required_skills": ["Python", "FastAPI", "PyTorch"]},
            "description": "Build high performance AI API microservices.",
            "status": "Published"
        }
    )
    job_id = job["id"]
    print(f"PASS: Recruiter created, Company created, Published Job created (Job ID: {job_id})")

    # 2. Setup Candidate & Active Resume
    print("\n2. Setting up Candidate User & Active Resume in MongoDB Atlas...")
    await db["users"].delete_many({"email": "candidate.phase3@example.com"})
    candidate_doc = {
        "name": "Phase 3 Candidate",
        "email": "candidate.phase3@example.com",
        "password_hash": pwd_context.hash("Password123!"),
        "role": "candidate",
        "email_verified": True,
        "profile_completed": True
    }
    candidate_res = await db["users"].insert_one(candidate_doc)
    candidate_id = str(candidate_res.inserted_id)

    await db["resumes"].delete_many({"user_id": candidate_id})
    resume_doc = {
        "user_id": candidate_id,
        "filename": "Candidate_Resume_v1.pdf",
        "file_url": "/static/resumes/test.pdf",
        "raw_text": "Experienced Python and FastAPI Developer with PyTorch expertise.",
        "skills": ["Python", "FastAPI", "PyTorch"],
        "created_at": datetime.now(timezone.utc)
    }
    resume_res = await db["resumes"].insert_one(resume_doc)
    resume_id = str(resume_res.inserted_id)
    print(f"PASS: Candidate created (ID: {candidate_id}), Active Resume created (ID: {resume_id})")

    # 3. Test Candidate Published Jobs Discovery
    print("\n3. Testing Candidate Job Discovery (GET /api/v1/jobs)...")
    published_jobs = await get_published_jobs(search="AI Backend", candidate_id=candidate_id)
    print(f"PASS: Retrieved {len(published_jobs)} published job(s)")
    assert len(published_jobs) >= 1
    assert published_jobs[0]["id"] == job_id
    assert published_jobs[0]["has_applied"] is False

    # 4. Test Application Submission Flow
    print("\n4. Testing Candidate Application Submission (POST /api/v1/applications)...")
    app_doc = await create_application(
        candidate_id=candidate_id,
        job_id=job_id,
        notes="Excited to apply for the Senior AI Backend Engineer role."
    )
    print(f"PASS: Application created in MongoDB Atlas! Application ID: {app_doc['id']}")
    assert app_doc["candidate_id"] == candidate_id
    assert app_doc["job_id"] == job_id
    assert app_doc["company_id"] == company_id
    assert app_doc["recruiter_id"] == recruiter_id
    assert app_doc["resume_version_id"] == resume_id
    assert app_doc["status"] == "Applied"

    # Verify Job applications_count incremented
    updated_job = await get_job_by_id(job_id)
    print(f"PASS: Job Requisition applications_count incremented to: {updated_job['applications_count']}")
    assert updated_job["applications_count"] == 1

    # Verify Candidate Notification generated
    notif = await db["notifications"].find_one({"user_id": candidate_id})
    print(f"PASS: Candidate In-App Notification created: '{notif['message']}'")
    assert notif is not None

    # 5. Test Duplicate Application Prevention
    print("\n5. Testing Duplicate Application Rejection...")
    try:
        await create_application(candidate_id=candidate_id, job_id=job_id)
        assert False, "ERROR: Should have rejected duplicate application!"
    except Exception as err:
        print(f"PASS: Duplicate application rejected with message: '{err.detail}'")

    # 6. Test Candidate Applications Listing (GET /api/v1/applications/me)
    print("\n6. Testing Candidate Applications Listing...")
    my_apps = await get_candidate_applications(candidate_id=candidate_id)
    print(f"PASS: Retrieved {len(my_apps)} application(s) for candidate")
    assert len(my_apps) == 1
    assert my_apps[0]["job"]["title"] == "Senior AI Backend Engineer"

    # 7. Test Application Withdrawal
    print("\n7. Testing Candidate Application Withdrawal...")
    withdrawn_app = await withdraw_application(app_doc["id"], candidate_id=candidate_id)
    print(f"PASS: Application status updated to '{withdrawn_app['status']}'")
    assert withdrawn_app["status"] == "Withdrawn"

    job_after_withdraw = await get_job_by_id(job_id)
    print(f"PASS: Job Requisition applications_count decremented to: {job_after_withdraw['applications_count']}")
    assert job_after_withdraw["applications_count"] == 0

    print("\n==========================================================")
    print("🎉 ALL PHASE 3 CANDIDATE APPLICATION TEST CONDITIONS PASSED 100%!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_phase3_candidate_applications())
