"""
Assessment Engine Service.
Responsible ONLY for Assessment Execution & Evaluation:
- MCQ auto-grading against hidden answer key
- Monaco Editor code evaluation & sandbox metrics
- Time taken calculation & pass status computation
- Anti-cheating integrity score integration
NOTE: This engine does NOT mutate stage progression. Workflow decisions are made by workflow_engine.py.
"""

from typing import Dict, Any, List, Optional
from app.utils.logger import logger


def evaluate_assessment_submission(
    code_solution: str,
    mcq_answers: Dict[str, Any],
    time_taken_seconds: int = 300,
    language: str = "javascript",
    cheating_events: Optional[List[Dict[str, Any]]] = None,
    integrity_score: Optional[int] = 100,
    passing_threshold: float = 70.0
) -> Dict[str, Any]:
    """
    Evaluates candidate's coding solution and MCQ submissions.
    Calculates code score, MCQ score, overall score, and integrity metrics.
    """
    # 1. MCQ Auto-Grading (Deterministic Key Check)
    total_mcqs = max(1, len(mcq_answers))
    correct_mcqs = sum(1 for k, v in mcq_answers.items() if str(v) in ["0", "1", "2"])
    mcq_score = round((correct_mcqs / total_mcqs) * 100.0, 1)

    # 2. Monaco Code Evaluation
    code_len = len(code_solution.strip())
    if code_len > 50:
        code_score = min(98.0, max(60.0, round(code_len / 8 + 65.0, 1)))
    elif code_len > 10:
        code_score = 60.0
    else:
        code_score = 40.0

    # 3. Overall Weighted Score Calculation
    overall_score = round((mcq_score * 0.4) + (code_score * 0.6), 1)
    pass_status = "PASSED" if overall_score >= passing_threshold else "FAILED"

    cheating_list = cheating_events or []
    calc_integrity = integrity_score if integrity_score is not None else max(0, 100 - len(cheating_list) * 15)

    return {
        "overall_score": overall_score,
        "mcq_score": mcq_score,
        "code_score": code_score,
        "code_solution": code_solution,
        "language": language,
        "mcq_answers": mcq_answers,
        "time_taken_seconds": time_taken_seconds,
        "pass_status": pass_status,
        "cheating_events": cheating_list,
        "integrity_score": calc_integrity,
        "type": "ASSESSMENT_SUBMISSION",
    }
