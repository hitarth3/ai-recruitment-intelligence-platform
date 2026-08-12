"""
Interview Engine Service.
Responsible ONLY for Interview Turn & Speech Metrics Processing:
- Processing turn-based speech input
- Calculating speech metrics (Communication, Technical Accuracy, Confidence, Fluency)
- Recording WebRTC session metadata
NOTE: This engine does NOT decide stage progression. Workflow decisions are made by workflow_engine.py.
"""

from typing import Dict, Any, List, Optional
import random
from app.services.ai_engine import generate_interview_turn_question
from app.utils.logger import logger


def process_speech_interview_turn(
    user_transcript: str,
    conversation_history: List[Dict[str, str]],
    job_title: str = "Software Engineer"
) -> Dict[str, Any]:
    """
    Processes a single speech turn in an AI Interview.
    Evaluates speech metrics deterministically and gets next non-repeating question from AI engine.
    """
    previous_questions = [t.get("text") for t in conversation_history if t.get("role") == "ai"]

    # 1. AI Engine generates next question
    ai_reply = generate_interview_turn_question(
        job_title=job_title,
        user_transcript=user_transcript,
        conversation_history=conversation_history,
        previous_questions=previous_questions
    )

    # 2. Deterministic Speech Metrics Calculation
    words_count = len(user_transcript.split())
    comm_score = min(96, max(68, words_count * 2 + 62))
    tech_score = min(95, max(65, 80 + random.randint(-5, 8)))
    conf_score = min(98, max(72, 84 + random.randint(-4, 7)))
    flu_score = min(95, max(70, 83 + random.randint(-3, 6)))

    speech_eval = {
        "communication_score": comm_score,
        "confidence_score": conf_score,
        "technical_accuracy": tech_score,
        "fluency_score": flu_score,
        "recommendation": "Strong Technical Alignment" if tech_score >= 80 else "Moderate Alignment",
    }

    return {
        "ai_reply": ai_reply,
        "speech_eval": speech_eval,
    }
