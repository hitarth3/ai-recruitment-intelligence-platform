"""
AI Engine Service.
Responsible ONLY for LLM (Groq) natural language interactions:
- Natural language resume fit explanations
- Interview question generation & follow-ups
- AI Career Coach responses & feedback
- Natural language recruiter summaries

CRITICAL RULE: This engine NEVER computes numerical scores directly.
All scores are computed deterministically by ml_engine.py.
"""

from typing import Dict, Any, List, Optional
from app.ai.gemini_service import gemini_service
from app.utils.logger import logger


def explain_resume_match(
    resume_skills: List[str],
    matched_skills: List[str],
    missing_skills: List[str],
    job_title: str,
    overall_score: float
) -> str:
    """Generates natural language fit explanation based on ML match metrics."""
    prompt = (
        f"You are an expert AI Technical Recruiter.\n"
        f"Candidate scored {overall_score}% overall fit for the role of '{job_title}'.\n"
        f"Matched Skills: {matched_skills}\n"
        f"Missing Skills: {missing_skills}\n"
        f"Provide a 2-3 sentence professional explanation summarizing candidate fit and key strengths."
    )
    try:
        explanation = gemini_service.generate_text(prompt)
        if explanation:
            return explanation
    except Exception as e:
        logger.error(f"[AIEngine] Failed to generate resume explanation: {e}")

    return (
        f"Candidate demonstrates {overall_score}% technical alignment for '{job_title}' with "
        f"strong proficiency in {', '.join(matched_skills[:3]) if matched_skills else 'core required skills'}."
    )


def generate_interview_turn_question(
    job_title: str,
    user_transcript: str,
    conversation_history: List[Dict[str, str]],
    previous_questions: List[str]
) -> str:
    """Generates next non-repeating dynamic interview question based on past turns."""
    prompt = (
        f"You are an expert AI Technical Recruiter conducting an interview for '{job_title}'.\n"
        f"Conversation History: {conversation_history[-6:]}\n"
        f"Previously Asked Questions (DO NOT REPEAT ANY OF THESE): {previous_questions}\n"
        f"Candidate's Answer: \"{user_transcript}\"\n\n"
        f"Rules:\n"
        f"1. Do NOT repeat any previously asked question.\n"
        f"2. Acknowledge candidate's technical response in 1 sentence.\n"
        f"3. Ask ONE relevant follow-up question assessing technical depth or problem solving."
    )
    try:
        reply = gemini_service.generate_text(prompt)
        if reply and not any(q.lower() in reply.lower() for q in previous_questions if len(q) > 10):
            return reply
    except Exception as e:
        logger.error(f"[AIEngine] Failed to generate interview turn question: {e}")

    return "Thank you for sharing that insight. Moving forward, how do you handle asynchronous error recovery and state persistence in distributed web services?"
