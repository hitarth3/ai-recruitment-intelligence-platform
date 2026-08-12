"""
Question Engine Service.
Responsible ONLY for Question Pool Management:
- Dynamic non-repeating question fetching from MongoDB Atlas collections:
  (technical_questions, mcq_questions, coding_questions, behavioral_questions, cloud_questions, sql_questions)
- Question pool seeding and category filtering
"""

from typing import List, Dict, Any, Optional
from app.database.question_pool_db import (
    get_random_mcq_questions,
    get_random_coding_question,
    seed_question_pools_if_empty
)
from app.utils.logger import logger


async def fetch_assessment_question_set(
    job_role: str = "Fullstack",
    required_skills: Optional[List[str]] = None,
    exclude_question_ids: Optional[List[str]] = None,
    mcq_count: int = 5
) -> Dict[str, Any]:
    """
    Fetches a non-repeating set of MCQ and Coding questions for a technical assessment.
    """
    await seed_question_pools_if_empty()
    exclude_ids = exclude_question_ids or []

    mcqs = await get_random_mcq_questions(
        role=job_role,
        skills=required_skills,
        exclude_ids=exclude_ids,
        limit=mcq_count
    )

    coding = await get_random_coding_question(
        role=job_role,
        exclude_ids=exclude_ids
    )

    return {
        "mcqs": mcqs,
        "coding_question": coding,
        "total_questions": len(mcqs) + 1,
    }
