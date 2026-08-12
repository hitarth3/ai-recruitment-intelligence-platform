"""
Anti-Cheat Engine Service.
Responsible ONLY for Browser Integrity Monitoring & Warning Analytics:
- Validating integrity event logs (tab switch, window blur, devtools, camera obscuration)
- Calculating integrity score: max(0, 100 - (events.length * 15))
- Generating recruiter warning timeline reports
"""

from typing import List, Dict, Any, Optional
from app.utils.logger import logger


def calculate_assessment_integrity(cheating_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates integrity score and generates structured warning report.
    """
    events = cheating_events or []
    event_count = len(events)
    integrity_score = max(0, 100 - event_count * 15)

    if integrity_score >= 90:
        status = "CLEAN_INTEGRITY"
        risk_level = "LOW"
    elif integrity_score >= 60:
        status = "MODERATE_WARNINGS"
        risk_level = "MEDIUM"
    else:
        status = "HIGH_SUSPICION"
        risk_level = "HIGH"

    return {
        "integrity_score": integrity_score,
        "total_warnings": event_count,
        "status": status,
        "risk_level": risk_level,
        "cheating_events": events,
    }
