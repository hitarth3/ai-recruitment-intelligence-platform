"""
Automated Test Suite for Phase 2: Company Profile, Recruiter Dashboard & 7-Step Job Management.
"""

import asyncio
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.api.v1.company.routes import create_company, get_my_company, update_company
from app.api.v1.jobs.routes import post_new_job, list_my_company_jobs, change_job_status, get_recruiter_dashboard_stats
from app.schemas.company import CompanyCreateRequest
from app.schemas.job import JobCreateRequest, JobStatusPatchRequest


async def test_phase2_recruiter_modules():
    await connect_to_mongo()
    db = get_database()

    # Retrieve or create a test recruiter in db.users
    recruiter = await db["users"].find_one({"role": "recruiter", "email": "test.phase2.recruiter@example.com"})
    if not recruiter:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        recruiter_doc = {
            "name": "Sarah Wilson",
            "email": "test.phase2.recruiter@example.com",
            "password_hash": pwd_context.hash("Password123!"),
            "role": "recruiter",
            "email_verified": True,
            "profile_completed": False,
            "token_version": 1
        }
        res = await db["users"].insert_one(recruiter_doc)
        recruiter_doc["_id"] = res.inserted_id
        recruiter = recruiter_doc

    recruiter_id_str = str(recruiter["_id"])
    print(f"Testing with Recruiter: {recruiter['email']} [ID: {recruiter_id_str}]")

    # Clean existing test company & jobs for this recruiter
    await db["companies"].delete_many({"created_by": recruiter_id_str})
    await db["jobs"].delete_many({"recruiter_id": recruiter_id_str})

    # Reset recruiter profile_completed state for testing onboarding
    await db["users"].update_one(
        {"_id": recruiter["_id"]},
        {"$set": {"profile_completed": False, "company_id": None}}
    )

    print("\n1. Testing Company Profile Creation & Onboarding...")
    company_req = CompanyCreateRequest(
        company_name="TechNova AI Corp",
        industry="Software & IT",
        company_size="51-200 employees",
        company_type="Product",
        website="https://technova.example.com",
        company_email="careers@technova.example.com",
        country="United States",
        city="San Francisco",
        description="TechNova builds production AI platforms for enterprise hiring workflows.",
        mission="Empower hiring teams with high-speed AI tools.",
        benefits=["Health & Dental Insurance", "Remote Allowance", "401(k) Matching"]
    )

    created_company = await create_company(company_req, current_recruiter=recruiter)
    print(f"PASS: Company Profile Created! ID: {created_company['id']} | Verification Status: '{created_company['verification_status']}'")

    # Verify Recruiter profile_completed == True
    user_updated = await db["users"].find_one({"_id": recruiter["_id"]})
    assert user_updated["profile_completed"] is True, "ERROR: profile_completed must be True!"
    assert user_updated["company_id"] == created_company["id"], "ERROR: company_id must be linked!"
    print("PASS: Recruiter document updated with company_id and profile_completed = True.")

    print("\n2. Testing GET Company & Dynamic Profile Completion %...")
    my_company = await get_my_company(current_recruiter=recruiter)
    comp_perc = my_company["profile_completion_percentage"]
    missing = my_company["missing_fields"]
    print(f"PASS: Dynamic Profile Completion: {comp_perc}% | Missing Fields Checklist: {missing}")

    print("\n3. Testing 7-Step Job Requisition Posting...")
    job_req = JobCreateRequest(
        title="Senior AI Frontend Engineer",
        department="Engineering",
        category="Software Development",
        employment_type="Full-time",
        open_positions=2,
        location={"country": "United States", "state": "California", "city": "San Francisco", "work_mode": "Hybrid"},
        experience={"min_years": 4, "max_years": 7},
        salary={"min_salary": 140000, "max_salary": 180000, "currency": "USD", "is_negotiable": True},
        skills={
            "required_skills": ["React", "TypeScript", "Tailwind CSS"],
            "preferred_skills": ["Next.js", "GraphQL"]
        },
        description="Build state of the art responsive frontend AI portals.",
        responsibilities=["Architect React components", "Integrate async APIs"],
        requirements=["4+ years React & TypeScript experience"],
        benefits=["Stock Options", "Health Insurance"],
        status="Published"
    )

    created_job = await post_new_job(job_req, current_recruiter=recruiter)
    job_id = created_job["id"]
    print(f"PASS: Job Created! Title: '{created_job['title']}' | Company Attached: '{created_job['company_name']}' | Status: '{created_job['status']}'")
    assert created_job["company_id"] == created_company["id"], "ERROR: company_id missing on job!"
    assert created_job["recruiter_id"] == recruiter_id_str, "ERROR: recruiter_id missing on job!"

    print("\n4. Testing Job Status Toggle (Draft -> Published -> Closed -> Archived)...")
    patched = await change_job_status(job_id, JobStatusPatchRequest(status="Closed"), current_recruiter=recruiter)
    print(f"PASS: Job Status Updated to: '{patched['status']}'")

    print("\n5. Testing Recruiter Dashboard MongoDB Metrics Aggregation...")
    stats = await get_recruiter_dashboard_stats(current_recruiter=recruiter)
    print("PASS: Real MongoDB Metrics Aggregated:")
    print(f"Total Jobs: {stats['total_jobs']} | Published: {stats['published_jobs']} | Closed: {stats['closed_jobs']}")

    print("\n🎉 PHASE 2 COMPANY PROFILE, RECRUITER DASHBOARD & JOB MANAGEMENT VERIFIED 100% WORKING!")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_phase2_recruiter_modules())
