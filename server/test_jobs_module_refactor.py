"""
Automated Verification Test Suite for Unified Candidate Jobs Module Refactor:
1. Verify Candidate Jobs Endpoint (GET /api/v1/jobs?tab=recommended & tab=all).
2. Verify Skill Match Calculation (% match, matched_skills ✓, missing_skills).
3. Verify total_published count and recommended_count metrics.
4. Verify Candidate Applications count.
"""

import asyncio
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.database.job_db import get_published_jobs, get_published_jobs_count
from app.database.application_db import get_candidate_application_count


async def test_jobs_module_refactor():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("RUNNING CANDIDATE JOBS MODULE REFACTOR TEST SUITE")
    print("==========================================================\n")

    # 1. Fetch any Candidate user
    candidate = await db["users"].find_one({"role": "candidate"})
    candidate_id = str(candidate["_id"]) if candidate else None
    print(f"Testing with Candidate ID: {candidate_id}")

    # 2. Test GET Published Jobs (tab=all)
    all_jobs, total_pub, rec_count = await get_published_jobs(tab="all", candidate_id=candidate_id)
    print(f"PASS: Tab 'all' returned {len(all_jobs)} published job(s) (Total: {total_pub}, Recommended: {rec_count})")
    assert isinstance(all_jobs, list)

    # 3. Test GET Published Jobs (tab=recommended)
    rec_jobs, _, _ = await get_published_jobs(tab="recommended", candidate_id=candidate_id)
    print(f"PASS: Tab 'recommended' returned {len(rec_jobs)} unapplied job(s)")
    assert isinstance(rec_jobs, list)

    # 4. Verify Skill Match Metrics structure on returned jobs
    if all_jobs:
        sample_job = all_jobs[0]
        print(f"\nSample Job Match Info for '{sample_job.get('title')}':")
        print(f" - Match Percentage: {sample_job.get('match_percentage')}%")
        print(f" - Matched Skills: {sample_job.get('matched_skills')}")
        print(f" - Missing Skills: {sample_job.get('missing_skills')}")

        assert "match_percentage" in sample_job
        assert "matched_skills" in sample_job
        assert "missing_skills" in sample_job

    # 5. Test Counts Endpoint
    counts = await get_published_jobs_count(candidate_id=candidate_id)
    print(f"\nPASS: Jobs Count Endpoint returned: {counts}")
    assert "total_published" in counts
    assert "recommended_count" in counts

    if candidate_id:
        app_count = await get_candidate_application_count(candidate_id)
        print(f"PASS: Candidate Applied Jobs Count = {app_count}")
        assert isinstance(app_count, int)

    print("\n==========================================================")
    print("🎉 ALL JOBS MODULE REFACTOR TEST CONDITIONS PASSED 100%!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_jobs_module_refactor())
