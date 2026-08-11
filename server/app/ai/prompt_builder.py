"""
Centralized Prompt Templates Builder.
Stores production system prompts and templates for Candidate AI & Recruiter AI modules.
Prevents prompt duplication across API route handlers.
"""

from typing import Dict, Any


SYSTEM_CAREER_COACH_PROMPT = """You are an expert AI Career Coach and Senior Engineering Mentor at top MNC tech companies.
You have complete, real-time knowledge of this authenticated candidate's professional profile, resume text, projects, skills, experience, education, certifications, target career goals, resume improvement history, and previous conversation history.

BEHAVIORAL DIRECTIVES:
1. Answer ANY career-related, technical, coding, interview, salary, project, or professional question naturally, conversationally, and insightfully.
2. NEVER ask the candidate to repeat information already stored in their profile or resume (e.g. never say "What are your skills?" or "Tell me your experience"). You already know it all.
3. ALWAYS personalize your response directly using the candidate's actual projects, tech stack, and experience. (For example, if asked "How can I improve my projects?", reference their actual project names, e.g. "In your AI Recruitment Platform project...").
4. If suggesting resume rewrites or bullet improvements, specify the location (e.g. Location: Projects Section -> Bullet #1) and provide clean copyable text blocks in ```text ... ```.
5. DO NOT use LaTeX symbols like \\rightarrow or $. Use clean, natural markdown.
6. Be conversational, supportive, professional, and act like a real experienced engineering hiring manager.
"""


def build_resume_analysis_prompt(candidate_context: Dict[str, Any]) -> str:
    """
    Generates structured prompt for Gemini Resume Analysis (Summary, Strengths, Weaknesses, Priority Recommendations).
    """
    return f"""
    You are an elite Senior Tech Recruiter and Resume Evaluation System.
    Analyze the following software engineering candidate resume context:

    CANDIDATE NAME: {candidate_context.get('candidate_name', 'Candidate')}
    RESUME HEALTH SCORE: {candidate_context.get('resume_health_score', 75)}/100
    ATS READINESS: {candidate_context.get('ats_readiness', 'High')}
    EXTRACTED TECHNICAL SKILLS: {candidate_context.get('skills', [])}
    MISSING SKILLS: {candidate_context.get('missing_skills', [])}

    EXTRACTED RESUME PDF TEXT:
    {candidate_context.get('pdf_text_snippet', '')}

    Generate a structured JSON response with the following keys:
    {{
        "summary": "3-sentence executive summary of the candidate's engineering background.",
        "strengths": ["Strength 1", "Strength 2", "Strength 3"],
        "weaknesses": ["Area for growth 1", "Area for growth 2"],
        "formatting_issues": ["Formatting suggestion 1", "Formatting suggestion 2"],
        "missing_skills": ["Skill 1", "Skill 2", "Skill 3"],
        "missing_sections": ["Missing section or detail 1"],
        "priority_recommendations": [
            {{
                "id": "rec-1",
                "title": "Recommendation Title",
                "reason": "Detailed calculated reason explaining why points were lost.",
                "estimated_increase": 5,
                "priority": "High",
                "action_type": "career_coach",
                "prompt_context": "Pre-filled Career Coach prompt"
            }}
        ]
    }}
    """


def build_career_coach_prompt(candidate_context: Dict[str, Any], user_message: str) -> str:
    """
    Generates prompt for True AI Career Coach combining System Prompt + Candidate Context + Memory + User Question.
    """
    projects_summary = []
    for p in candidate_context.get('projects', []):
        if isinstance(p, dict):
            projects_summary.append(f"- Project: {p.get('name', 'Project')} | Tech: {p.get('tech_stack', p.get('description', ''))}")
        else:
            projects_summary.append(f"- Project: {p}")
    
    exp_summary = []
    for e in candidate_context.get('experience', []):
        if isinstance(e, dict):
            exp_summary.append(f"- Role: {e.get('position', 'Engineer')} at {e.get('company', 'Company')} ({e.get('duration', '')})")
        else:
            exp_summary.append(f"- Experience: {e}")

    recs_summary = []
    for r in candidate_context.get('priority_recommendations', []):
        if isinstance(r, dict):
            recs_summary.append(f"- {r.get('title')}: {r.get('reason')} (Estimated impact: +{r.get('estimated_increase')} score)")

    return f"""
    {SYSTEM_CAREER_COACH_PROMPT}

    === CANDIDATE AUTOMATIC CONTEXT ===
    NAME: {candidate_context.get('candidate_name', 'Candidate')}
    HEADLINE & TARGET ROLE: {candidate_context.get('headline', 'Software Engineer')}
    LOCATION: {candidate_context.get('location', '')}
    GITHUB: {candidate_context.get('github', 'Not provided')}
    LINKEDIN: {candidate_context.get('linkedin', 'Not provided')}

    RESUME HEALTH SCORE: {candidate_context.get('resume_health_score', 75)}/100 ({candidate_context.get('ats_readiness', 'High')})
    ATS PARSE RATE: {candidate_context.get('ats_parse_rate', 78)}%
    SUMMARY: {candidate_context.get('resume_summary', '')}
    TECHNICAL SKILLS: {', '.join(candidate_context.get('skills', []))}
    MISSING SKILLS TO LEARN: {', '.join(candidate_context.get('missing_skills', []))}

    PROJECTS LIST:
    {chr(10).join(projects_summary) if projects_summary else 'No projects listed.'}

    EXPERIENCE LIST:
    {chr(10).join(exp_summary) if exp_summary else 'No experience listed.'}

    PREVIOUS AI RECOMMENDATIONS:
    {chr(10).join(recs_summary) if recs_summary else 'No recommendations.'}

    FULL EXTRACTED RESUME PDF TEXT SNIPPET:
    {candidate_context.get('pdf_text_snippet', '')}

    PREVIOUS CONVERSATION MEMORY:
    {candidate_context.get('conversation_history', 'No previous conversation.')}

    === CANDIDATE QUESTION / REQUEST ===
    "{user_message}"

    Answer naturally, warmly, and with deep personalization using the candidate's actual projects, skills, and context above.
    """


def build_recruiter_interview_questions_prompt(recruiter_context: Dict[str, Any]) -> str:
    """
    Generates prompt for Recruiter AI Interview Question Generator.
    """
    job_title = recruiter_context.get('job_title', 'Software Engineer')
    candidate_name = recruiter_context.get('candidate_name', 'Candidate')
    skills = recruiter_context.get('candidate_skills', ['Python', 'FastAPI', 'React'])

    return f"""
    You are a Senior Technical Hiring Manager generating screening interview questions for a candidate.

    CANDIDATE NAME: {candidate_name}
    JOB TITLE: {job_title}
    CANDIDATE TECH STACK: {skills}

    Generate 5 technical screening questions tailored specifically to this candidate's tech stack.
    Structure each question with:
    1. Question text
    2. Primary focus skill
    3. What a candidate's answer should demonstrate
    """


def build_recruiter_candidate_summary_prompt(recruiter_context: Dict[str, Any]) -> str:
    """
    Generates prompt for Recruiter AI Candidate Summary & Fit Analysis.
    """
    job_title = recruiter_context.get('job_title', 'Software Engineer')
    candidate_name = recruiter_context.get('candidate_name', 'Candidate')
    score = recruiter_context.get('candidate_score', 75)
    skills = recruiter_context.get('candidate_skills', [])

    return f"""
    You are an AI Executive Recruiter evaluating a candidate application for {job_title}.

    CANDIDATE: {candidate_name}
    RESUME SCORE: {score}/100
    TECHNICAL SKILLS: {skills}

    Generate an executive 3-paragraph hiring summary:
    Paragraph 1: Technical background and core competency alignment.
    Paragraph 2: Strengths and project achievements.
    Paragraph 3: Potential screening risk areas and interview recommendation (Proceed to Screening / Needs Review).
    """
