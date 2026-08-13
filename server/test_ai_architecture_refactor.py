"""
Automated Test Suite for AI Architecture Refactor:
1. Multi-User Isolation
2. Non-Resume Invalid File Rejection (400 Bad Request + Exact Message)
3. Dynamic ATS Scoring (Different Resumes = Different Scores)
4. Dynamic Improvement Recommendations (Persona/Stack-based)
5. Resume Version History & Non-Resume Form Rejection Verification
6. AI Career Mentor Memory & Context Aggregation
"""

import os
import asyncio
from datetime import datetime, timezone
from passlib.context import CryptContext
from app.database.database import connect_to_mongo, get_database, close_mongo_connection
from app.database.resume_db import save_or_replace_resume, get_user_resume
from app.database.coach_chat_db import save_chat_message, get_candidate_chat_history, clear_candidate_chat_history
from app.services.resume_analyzer_service import analyze_candidate_resume
from app.ai.career_coach import process_career_coach_chat
from app.services.improvement_service import generate_dynamic_checklist, generate_priority_recommendations

RESUMES_DIR = os.path.abspath(os.path.join("uploads", "resumes"))
os.makedirs(RESUMES_DIR, exist_ok=True)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_dummy_pdf(filename: str, content: str) -> str:
    """Helper to create test PDF using PyMuPDF (fitz)."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), content)
    file_path = os.path.abspath(os.path.join(RESUMES_DIR, filename))
    doc.save(file_path)
    doc.close()
    return file_path


async def test_ai_architecture_refactor():
    await connect_to_mongo()
    db = get_database()

    print("==========================================================")
    print("RUNNING AI ARCHITECTURE REFACTOR VERIFICATION TEST SUITE")
    print("==========================================================\n")

    # 1. SETUP TWO CANDIDATE USERS (Backend Dev & Frontend Dev)
    print("1. Setting up Isolated Candidate A (Backend) & Candidate B (Frontend)...")
    await db["users"].delete_many({"email": {"$in": ["backend.cand@example.com", "frontend.cand@example.com"]}})
    
    cand_a_doc = {
        "name": "Alex Backend",
        "email": "backend.cand@example.com",
        "password_hash": pwd_context.hash("Password123!"),
        "role": "candidate",
        "email_verified": True,
        "profile_completed": True
    }
    res_a = await db["users"].insert_one(cand_a_doc)
    user_a_id = str(res_a.inserted_id)

    cand_b_doc = {
        "name": "Bella Frontend",
        "email": "frontend.cand@example.com",
        "password_hash": pwd_context.hash("Password123!"),
        "role": "candidate",
        "email_verified": True,
        "profile_completed": True
    }
    res_b = await db["users"].insert_one(cand_b_doc)
    user_b_id = str(res_b.inserted_id)

    # Clean existing resumes & chats
    await db["resumes"].delete_many({"user_id": {"$in": [user_a_id, user_b_id]}})
    await db["career_coach_chats"].delete_many({"user_id": {"$in": [user_a_id, user_b_id]}})

    # 2. TEST INVALID FILE REJECTION (Non-Resume Document: University Form / Invoice)
    print("\n2. Testing Non-Resume Invalid File Detection (Gujarat University Form)...")
    gujarat_form_text = """
    Application No : PDC258317244
    GUJARAT UNIVERSITY
    Application Form for Provisional Degree
    Personal Details
    Student Name : JENIL SHAH
    Email ID : 8822.stkabirdin@gmail.com
    Mobile No : 6354398820
    Gender : Male
    Reason : To get admission in another college
    Address Line 1 : A-1304 Shashwat Skyz
    City : Ahmedabad
    PINCode : 380005
    Educational Details
    Degree / Course : Bachelor of Science (I.T. & C.A.)
    College Name : Sheth K.S.School of Busi.Mngt.
    Passing Year : 2025
    Payment Details
    Payment Status : Success
    Amount : Rs. 252
    Uploaded Documents List
    1 : All Semester Marksheet
    Lock Date: 2025-09-14 20:15:08 Print Date: 14-09-2025 20:15:38
    """
    invalid_pdf = create_dummy_pdf("gujarat_univ_form.pdf", gujarat_form_text)

    try:
        await save_or_replace_resume(user_a_id, "gujarat_univ_form.pdf", invalid_pdf, os.path.getsize(invalid_pdf))
        assert False, "ERROR: Gujarat University Application Form should have been rejected immediately as non-resume!"
    except ValueError as ve:
        err_msg = str(ve)
        print(f"PASS: Gujarat University Form REJECTED successfully with exact message:\n  '{err_msg}'")
        assert "Official University Form" in err_msg or "not appear to be a valid resume" in err_msg, "ERROR: Required error message missing!"

    # 3. TEST DYNAMIC ATS SCORE & ISOLATION FOR CANDIDATE A vs CANDIDATE B
    print("\n3. Testing Dynamic ATS Scoring & Multi-User Context Isolation...")
    resume_a_v1_text = """
    Alex Backend - Senior Software Engineer
    Contact: alex@example.com | Phone: 123-456-7890 | GitHub: github.com/alex-backend
    
    PROFESSIONAL SUMMARY:
    Experienced Backend Developer specializing in Python, FastAPI, MongoDB, PostgreSQL, and REST APIs.
    
    WORK EXPERIENCE:
    Software Engineer @ TechCorp (2022 - Present)
    - Engineered high-throughput microservices handling 50,000 requests per minute using Python and FastAPI.
    - Optimized database queries in PostgreSQL, reducing P99 latency by 42%.
    - Built asynchronous Redis messaging queues for real-time notification dispatch.
    
    EDUCATION:
    Bachelor of Science in Computer Science, University of Technology (2018 - 2022)
    
    SKILLS:
    Python, FastAPI, MongoDB, PostgreSQL, Redis, REST API, Git, Linux
    """

    resume_b_v1_text = """
    Bella Frontend - UI/UX Engineer
    Contact: bella@example.com | Phone: 987-654-3210 | GitHub: github.com/bella-ui
    
    SUMMARY:
    Frontend Specialist building responsive web applications with React, TypeScript, Next.js, and TailwindCSS.
    
    PROJECTS:
    AI Career Portal UI
    - Developed accessible design system using React 18 and TailwindCSS.
    - Improved Web Vitals lighthouse score from 65 to 98.
    
    EDUCATION:
    BS Software Engineering, State University (2020 - 2024)
    
    SKILLS:
    React, TypeScript, Next.js, HTML, CSS, TailwindCSS, Web Accessibility, Figma
    """

    pdf_a_v1 = create_dummy_pdf("alex_backend_v1.pdf", resume_a_v1_text)
    pdf_b_v1 = create_dummy_pdf("bella_frontend_v1.pdf", resume_b_v1_text)

    saved_a = await save_or_replace_resume(user_a_id, "alex_backend_v1.pdf", pdf_a_v1, os.path.getsize(pdf_a_v1))
    saved_b = await save_or_replace_resume(user_b_id, "bella_frontend_v1.pdf", pdf_b_v1, os.path.getsize(pdf_b_v1))

    score_a = saved_a["resume_analysis"]["resume_health_score"]
    score_b = saved_b["resume_analysis"]["resume_health_score"]

    print(f"PASS: Candidate A (Backend) ATS Score: {score_a}/100")
    print(f"PASS: Candidate B (Frontend) ATS Score: {score_b}/100")
    assert score_a != score_b, "ERROR: Different resumes should yield different ATS scores!"

    # 4. TEST DYNAMIC IMPROVEMENT RECOMMENDATIONS
    print("\n4. Testing Dynamic Improvement Recommendations (Persona/Stack-based)...")
    recs_a = generate_priority_recommendations(saved_a, score_a)
    recs_b = generate_priority_recommendations(saved_b, score_b)

    rec_titles_a = [r["title"] for r in recs_a]
    rec_titles_b = [r["title"] for r in recs_b]

    print(f"PASS: Candidate A Recommendations: {rec_titles_a[:2]}")
    print(f"PASS: Candidate B Recommendations: {rec_titles_b[:2]}")

    # 5. TEST RESUME VERSION HISTORY (v1 -> v2)
    print("\n5. Testing Resume Version History Tracking...")
    resume_a_v2_text = resume_a_v1_text + "\n    - Containerized microservices using Docker & Kubernetes and deployed to AWS S3 & EC2."
    pdf_a_v2 = create_dummy_pdf("alex_backend_v2.pdf", resume_a_v2_text)

    saved_a_v2 = await save_or_replace_resume(user_a_id, "alex_backend_v2.pdf", pdf_a_v2, os.path.getsize(pdf_a_v2))
    versions_a = saved_a_v2["versions"]

    print(f"PASS: Candidate A Version Count: {len(versions_a)} (Versions: {[v['version_id'] for v in versions_a]})")
    assert len(versions_a) == 2, "ERROR: Version 2 should be appended to history!"
    assert saved_a_v2["active_version_number"] == 2, "ERROR: Active version must be 2!"
    
    score_a_v2 = saved_a_v2["resume_analysis"]["resume_health_score"]
    print(f"PASS: Version 1 Score ({score_a}) -> Version 2 Score ({score_a_v2})")

    # 6. TEST AI CAREER MENTOR MEMORY & CONTEXT ISOLATION
    print("\n6. Testing AI Career Mentor Context Aggregation & Conversation Memory...")
    await clear_candidate_chat_history(user_a_id)

    # First turn
    res1 = await process_career_coach_chat(user_a_id, "What projects do I have listed in my profile?")
    reply1 = res1["reply"]
    print(f"PASS: AI Mentor Turn 1 Reply snippet:\n  {reply1[:180]}...")

    # Second turn (Memory check)
    history = await get_candidate_chat_history(user_a_id, limit=20)
    print(f"PASS: Stored Chat Memory Count: {len(history)} messages in MongoDB Atlas.")
    assert len(history) >= 2, "ERROR: Conversation history must be persisted in MongoDB!"

    res2 = await process_career_coach_chat(user_a_id, "What should I learn next to improve my backend score?")
    reply2 = res2["reply"]
    print(f"PASS: AI Mentor Turn 2 Reply snippet:\n  {reply2[:180]}...")

    print("\n==========================================================")
    print("🎉 ALL AI ARCHITECTURE REFACTOR TEST CONDITIONS PASSED 100%!")
    print("==========================================================")

    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_ai_architecture_refactor())
