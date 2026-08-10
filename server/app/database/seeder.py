"""
MongoDB Atlas Auto-Seeder Module.
Ensures default demo Candidate and Recruiter accounts exist in MongoDB Atlas for instant testing.
"""

from app.database.auth_db import find_user_by_email, create_candidate, create_recruiter
from app.utils.logger import logger


async def seed_default_users():
    """
    Seeds default demo Candidate and Recruiter accounts if they do not exist in MongoDB Atlas.
    Default Candidate: alex.rivera@example.com / password123
    Default Recruiter: sarah.wilson@technova.example.com / password123
    """
    # 1. Seed Demo Candidate
    candidate = await find_user_by_email("alex.rivera@example.com")
    if not candidate:
        await create_candidate({
            "name": "Alex Rivera",
            "email": "alex.rivera@example.com",
            "password": "password123",
            "phone": "+1 (555) 019-2834",
            "location": "San Francisco, CA",
            "github": "https://github.com/alexrivera",
            "linkedin": "https://linkedin.com/in/alexrivera",
            "portfolio": "https://alexrivera.dev"
        })
        logger.info("🌱 Seeded default demo Candidate account: alex.rivera@example.com")

    # 2. Seed Demo Recruiter & Company
    recruiter = await find_user_by_email("sarah.wilson@technova.example.com")
    if not recruiter:
        await create_recruiter({
            "name": "Sarah Wilson",
            "email": "sarah.wilson@technova.example.com",
            "password": "password123",
            "company_name": "TechNova Solutions",
            "designation": "Senior Technical Recruiter",
            "company_website": "https://technova.example.com",
            "company_size": "250+ Employees",
            "industry": "Enterprise Software & Cloud Systems",
            "location": "San Francisco, CA (Hybrid)"
        })
        logger.info("🌱 Seeded default demo Recruiter account: sarah.wilson@technova.example.com")
