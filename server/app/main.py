"""
Main FastAPI Application Entry Point.
Sets up the API instance, CORS middleware, static file mounting, lifespan database connection, and module endpoints.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.database.database import connect_to_mongo, close_mongo_connection
from app.database.notification_db import ensure_notification_indexes
from app.utils.logger import logger

# Import Module Routers
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.candidate.profile import router as candidate_profile_router
from app.api.v1.candidate.settings import router as candidate_settings_router
from app.api.v1.resume.routes import router as resume_router
from app.api.v1.resume.analysis_routes import router as resume_analysis_router
from app.api.v1.resume.improvement_routes import router as resume_improvement_router
from app.api.v1.career.coach_routes import router as career_coach_router
from app.api.v1.notifications.routes import router as notification_router
from app.api.v1.company.routes import company_router
from app.api.v1.jobs.routes import job_router
from app.api.v1.applications.routes import applications_router
from app.api.v1.recruiter.candidates_routes import recruiter_candidates_router
from app.api.v1.talent.routes import talent_router
from app.api.v1.hiring_workflow.routes import hiring_workflow_router
from app.api.v1.sessions.routes import sessions_router
from app.api.v1.recruiter.studio_routes import studio_router
from app.api.v1.candidate.execution_routes import candidate_execution_router
from app.api.v1.workflow.routes import workflow_router

# Ensure required upload directories exist BEFORE mounting static files
AVATARS_DIR = os.path.join("uploads", "avatars")
RESUMES_DIR = os.path.join("uploads", "resumes")
os.makedirs(AVATARS_DIR, exist_ok=True)
os.makedirs(RESUMES_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Connects to MongoDB Atlas during startup, ensures database indexes, and closes connection during shutdown.
    """
    logger.info("Application starting up...")
    
    # Attempt connection to MongoDB Atlas
    await connect_to_mongo()
    await ensure_notification_indexes()
    
    yield  # Application runs while suspended here
    
    # Graceful shutdown handler
    logger.info("Application shutting down...")
    await close_mongo_connection()


# Initialize FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Recruitment Intelligence Platform API - Recruiter Intelligence Workspace Active",
    version="9.0.0",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

# Mount Static Files for Uploaded Avatars
app.mount("/static/avatars", StaticFiles(directory=AVATARS_DIR), name="static_avatars")

# Register API Module Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(auth_router)
app.include_router(candidate_profile_router, prefix="/api/v1")
app.include_router(candidate_settings_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1")
app.include_router(resume_analysis_router, prefix="/api/v1")
app.include_router(resume_improvement_router, prefix="/api/v1")
app.include_router(career_coach_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")
app.include_router(job_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(recruiter_candidates_router, prefix="/api/v1")
app.include_router(talent_router, prefix="/api/v1")
app.include_router(hiring_workflow_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(studio_router, prefix="/api/v1")
app.include_router(candidate_execution_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")


@app.get("/", summary="Root Endpoint")
async def root():
    """
    Root endpoint returning general API confirmation.
    """
    return {"message": "AI Recruitment Platform API Running - Candidate Settings & Layout Active"}


@app.get("/health", summary="Health Check Endpoint")
async def health_check():
    """
    Health check endpoint returning system operational status.
    """
    return {"status": "healthy"}
