"""
Portfolio Engine Service.
Responsible ONLY for Candidate Portfolio & Project Review Evaluation:
- Parsing GitHub URLs, LinkedIn links, live project demos, and PDF portfolio files
- Computing portfolio completeness score
"""

from typing import Dict, Any, List, Optional
from app.utils.logger import logger


def evaluate_candidate_portfolio(
    portfolio_url: Optional[str] = None,
    github_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    projects: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Evaluates candidate's portfolio completeness and technical project highlights.
    """
    projects_list = projects or []
    has_github = bool(github_url and "github.com" in github_url)
    has_linkedin = bool(linkedin_url and "linkedin.com" in linkedin_url)
    has_portfolio = bool(portfolio_url and len(portfolio_url) > 5)

    score = 50.0
    if has_github:
        score += 20.0
    if has_portfolio:
        score += 15.0
    if has_linkedin:
        score += 10.0
    if len(projects_list) > 0:
        score += min(15.0, len(projects_list) * 5.0)

    score = min(100.0, score)

    return {
        "portfolio_completeness_score": score,
        "has_github": has_github,
        "has_linkedin": has_linkedin,
        "has_portfolio": has_portfolio,
        "projects_count": len(projects_list),
        "status": "EVALUATED",
    }
