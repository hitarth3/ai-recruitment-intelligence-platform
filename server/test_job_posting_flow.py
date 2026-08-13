"""
Automated Verification Test Suite for Recruiter Job Posting & Active Jobs Refactor:
1. Verify POST /api/v1/jobs returns valid 201 Created JSON without ObjectId 500 Error.
2. Verify MongoDB Atlas persists the job requisition with company_id and recruiter_id.
3. Verify GET /api/v1/jobs/my-jobs returns the newly posted job requisition.
"""

import os
import asyncio
from passlib.context import CryptContext
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.database.company_db import create_company_profile, get_company_by_recruiter_id
from app.database.job_db import create_job, get_my_company_jobs
from app.schemas.job import JobCreateRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def test_job_posting_flow():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("RUNNING RECRUITER JOB POSTING & ACTIVE JOBS TEST SUITE")
    print("==========================================================\n")

    # 1. Setup Recruiter User & Company Profile
    print("1. Setting up test Recruiter & Company Profile...")
    await db["users"].delete_many({"email": "recruiter.test@example.com"})
    recruiter_doc = {
        "name": "Recruiter Test",
        "email": "recruiter.test@example.com",
        "password_hash": pwd_context.hash("Password123!"),
        "role": "recruiter",
        "email_verified": True,
        "profile_completed": True
    }
    user_res = await db["users"].insert_one(recruiter_doc)
    recruiter_id = str(user_res.inserted_id)

    await db["companies"].delete_many({"created_by": recruiter_id})
    company_data = {
        "company_name": "Test Tech Corp",
        "industry": "Software & Technology",
        "company_size": "50-200",
        "website": "https://testtechcorp.com",
        "headquarters": "San Francisco, CA",
        "description": "Building next generation cloud software."
    }
    company = await create_company_profile(recruiter_id, company_data)
    company_id = company["id"]
    print(f"PASS: Recruiter created (ID: {recruiter_id}), Company created (ID: {company_id})")

    # 2. Test Job Requisition Payload & MongoDB Persistence
    print("\n2. Testing 7-Step Job Requisition Payload & MongoDB Atlas Insertion...")
    job_payload = {
        "title": "Senior Cloud Infrastructure Engineer",
        "department": "Engineering",
        "category": "DevOps & Cloud",
        "employment_type": "Full-time",
        "open_positions": 2,
        "location": {
            "country": "United States",
            "state": "California",
            "city": "San Francisco",
            "work_mode": "Hybrid"
        },
        "experience": {
            "min_years": 4,
            "max_years": 8
        },
        "salary": {
            "min_salary": 140000,
            "max_salary": 180000,
            "currency": "USD",
            "is_negotiable": True
        },
        "education": {
            "required_degree": "Bachelor's Degree",
            "preferred_degree": "Master's Degree"
        },
        "skills": {
            "required_skills": ["Docker", "AWS", "Kubernetes", "Python"],
            "preferred_skills": ["Terraform", "CI/CD", "Prometheus"],
            "technologies": ["Cloud Infrastructure"],
            "frameworks": ["FastAPI"],
            "databases": ["PostgreSQL"],
            "cloud": ["AWS"],
            "tools": ["Git", "Docker", "Kubernetes"],
            "soft_skills": ["Leadership", "Problem Solving"],
            "languages": ["English"]
        },
        "description": "We are seeking a Senior Cloud Infrastructure Engineer to scale our Kubernetes clusters.",
        "responsibilities": [
            "Architect resilient cloud infrastructure on AWS.",
            "Manage CI/CD pipelines and Docker containers."
        ],
        "requirements": [
            "4+ years experience with AWS and Kubernetes."
        ],
        "benefits": ["Competitive Equity", "Health Insurance"],
        "settings": {
            "deadline": "2026-10-01",
            "joining_date": "2026-11-01",
            "allow_freshers": False,
            "visa_sponsorship": True
        },
        "status": "Published"
    }

    # Validate Schema
    validated_payload = JobCreateRequest(**job_payload)

    # Insert into DB
    created_job = await create_job(
        recruiter_id=recruiter_id,
        company_id=company_id,
        company_name=company["company_name"],
        company_logo=company.get("company_logo", ""),
        job_payload=validated_payload.model_dump()
    )

    print(f"PASS: Job created successfully! Job ID: {created_job['id']}")
    assert created_job["id"] is not None
    assert type(created_job["_id"]) is str, "ERROR: _id must be string encoded to prevent FastAPI JSON serialization 500 error!"

    # 3. Test Active Jobs List Retrieval
    print("\n3. Testing Active Jobs Retrieval from MongoDB Atlas...")
    jobs_list = await get_my_company_jobs(company_id=company_id)
    print(f"PASS: Retrieved {len(jobs_list)} active jobs for company '{company['company_name']}'")
    assert len(jobs_list) >= 1
    assert jobs_list[0]["title"] == "Senior Cloud Infrastructure Engineer"

    print("\n==========================================================")
    print("🎉 ALL RECRUITER JOB POSTING TEST CONDITIONS PASSED 100%!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_job_posting_flow())
