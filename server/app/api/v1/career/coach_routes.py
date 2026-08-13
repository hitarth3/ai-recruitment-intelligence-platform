"""
FastAPI REST API Router for AI Career Coach (True AI Assistant).
Endpoints:
- POST /api/v1/career/coach/chat (Send chat message to AI Career Coach)
- GET  /api/v1/career/coach/history (Retrieve conversation memory history from MongoDB Atlas)
- DELETE /api/v1/career/coach/history (Clear conversation memory history)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.api.v1.auth.dependencies import get_current_candidate
from app.ai.career_coach import process_career_coach_chat
from app.database.coach_chat_db import get_candidate_chat_history, clear_candidate_chat_history
from app.utils.logger import logger

router = APIRouter(prefix="/career/coach", tags=["Candidate AI Career Coach"])


@router.post("/chat", summary="Conversational AI Career Coach Chat")
async def chat_with_career_coach(
    message: str = Body(..., embed=True),
    current_candidate: dict = Depends(get_current_candidate)
):
    """
    Handles conversational AI mentor interactions.
    Automatically fetches complete CandidateContext (Profile, Resume, Projects, Skills, History) from MongoDB Atlas.
    Candidate never needs to type information already available in the platform.
    """
    user_id = current_candidate["id"]
    if not message or not message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    result = await process_career_coach_chat(user_id, message.strip())
    
    return {
        "reply": result["reply"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_context": result.get("candidate_context", {})
    }


@router.get("/history", summary="Get Candidate Chat History Memory")
async def get_chat_history(current_candidate: dict = Depends(get_current_candidate)):
    """
    Retrieves stored conversation history memory from MongoDB Atlas.
    """
    user_id = current_candidate["id"]
    messages = await get_candidate_chat_history(user_id, limit=50)
    return {"messages": messages}


@router.delete("/history", summary="Clear Candidate Chat History Memory")
async def clear_chat_history(current_candidate: dict = Depends(get_current_candidate)):
    """
    Clears candidate conversation memory in MongoDB Atlas.
    """
    user_id = current_candidate["id"]
    await clear_candidate_chat_history(user_id)
    return {"message": "Chat history cleared successfully."}
