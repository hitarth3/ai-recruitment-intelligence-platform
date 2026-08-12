"""
Centralized Workflow Engine Service.
The heart of the AI Recruitment Intelligence Platform.

Responsibilities:
- Initialize candidate workflow on application submission
- Advance stages (Approve & Advance)
- Reject candidates and auto-archive to hiring history
- Skip, repeat, and move stages
- Append timeline events (immutable audit trail)
- Generate notifications for recruiter and candidate
- Synchronize Recruitment Studio + Candidate Dashboard
- Archive selected/rejected candidates to hiring_history
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from app.database.database import get_database
from app.database.notification_db import insert_notification
from app.utils.logger import logger

# Engine type mapping: stage_name -> engine_type
ENGINE_MAP = {
    "AI Resume Screening": "Resume Engine",
    "Manual Resume Review": "Resume Engine",
    "Technical Assessment": "Assessment Engine",
    "AI Interview": "Interview Engine",
    "Technical Interview": "Interview Engine",
    "HR Round": "Interview Engine",
    "Portfolio Review": "Portfolio Engine",
    "Offer": "Offer Engine",
}


def get_engine_type(stage_name: str, stage_config: dict = None) -> str:
    """Determines execution engine from stage name or config."""
    if stage_config and stage_config.get("execution_engine"):
        return stage_config["execution_engine"]
    name_lower = stage_name.lower()
    if "resume" in name_lower or "screening" in name_lower:
        return "Resume Engine"
    if "assessment" in name_lower or "coding" in name_lower or "technical test" in name_lower:
        return "Assessment Engine"
    if "interview" in name_lower or "hr round" in name_lower or "hr interview" in name_lower:
        return "Interview Engine"
    if "portfolio" in name_lower:
        return "Portfolio Engine"
    if "offer" in name_lower:
        return "Offer Engine"
    return ENGINE_MAP.get(stage_name, "Assessment Engine")


def build_workflow_stages_from_job(job_workflow: List[Dict]) -> List[Dict]:
    """
    Transforms job hiring_workflow stages into candidate workflow stage objects.
    First stage -> Active, rest -> Pending.
    """
    stages = []
    enabled = [s for s in job_workflow if s.get("enabled", True)]
    # Sort by display_order
    enabled.sort(key=lambda s: s.get("display_order", 999))

    for idx, jstage in enumerate(enabled):
        stage_name = jstage.get("stage_name", "Stage")
        stages.append({
            "stage_id": jstage.get("stage_id", f"stage-{idx}"),
            "stage_name": stage_name,
            "engine_type": get_engine_type(stage_name, jstage.get("configuration", {})),
            "display_order": jstage.get("display_order", idx + 1),
            "configuration": jstage.get("configuration", {}),
            "evaluation_mode": jstage.get("evaluation_mode", "AI"),
            "status": "Active" if idx == 0 else "Pending",
            "execution_status": "Not Started" if idx == 0 else "Locked",
            "started_at": None,
            "completed_at": None,
            "execution_result": None,
            "recruiter_decision": None,
            "recruiter_notes": "",
        })
    return stages


def make_timeline_event(event_type: str, description: str, performed_by: str = "System", metadata: dict = None) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "description": description,
        "performed_by": performed_by,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }


def make_audit_entry(
    application_id: str, candidate_id: str, recruiter_id: str,
    company_id: str, job_id: str, stage_name: str,
    action: str, prev_status: str, new_status: str,
    performed_by: str, reason: str = ""
) -> dict:
    return {
        "entry_id": str(uuid.uuid4()),
        "application_id": application_id,
        "candidate_id": candidate_id,
        "recruiter_id": recruiter_id,
        "company_id": company_id,
        "job_id": job_id,
        "stage_name": stage_name,
        "action": action,
        "prev_status": prev_status,
        "new_status": new_status,
        "performed_by": performed_by,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def init_application_workflow(
    application_id: str,
    candidate_id: str,
    recruiter_id: str,
    company_id: str,
    job_id: str,
    job_title: str,
    company_name: str,
    job_workflow: List[Dict],
) -> Dict[str, Any]:
    """
    Called immediately when a candidate submits a job application.
    Reads job's configured hiring_workflow, builds candidate workflow stages,
    sets first stage Active, appends Applied timeline event, creates notifications.
    """
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()

    workflow_stages = build_workflow_stages_from_job(job_workflow)
    first_stage = workflow_stages[0] if workflow_stages else None
    current_stage_name = first_stage["stage_name"] if first_stage else "AI Resume Screening"

    # Build initial timeline
    timeline = [
        make_timeline_event("APPLIED", f"Candidate applied for '{job_title}' at {company_name}.", "Candidate"),
        make_timeline_event("WORKFLOW_INITIALIZED", f"Hiring workflow initialized. Starting with '{current_stage_name}'.", "System"),
    ]

    # Build initial audit log
    audit_log = [
        make_audit_entry(
            application_id, candidate_id, recruiter_id, company_id, job_id,
            current_stage_name, "APPLICATION_SUBMITTED", "None", "Applied", "Candidate"
        )
    ]

    # Update application with workflow data
    await db["applications"].update_one(
        {"_id": ObjectId(application_id)},
        {
            "$set": {
                "workflow_stages": workflow_stages,
                "current_stage": current_stage_name,
                "current_stage_status": "Active",
                "timeline": timeline,
                "audit_log": audit_log,
                "status": "Screening",
                "updated_at": datetime.now(timezone.utc),
            }
        }
    )

    # Recruiter notification
    await insert_notification({
        "user_id": recruiter_id,
        "type": "APPLICATION",
        "category": "Applications",
        "priority": "High",
        "title": "New Application Received",
        "message": f"A new candidate has applied for '{job_title}'. Review their profile in Recruitment Studio.",
        "action_type": "OPEN_STUDIO",
        "action_payload": {"job_id": job_id, "application_id": application_id},
        "source_module": "workflow_engine",
        "source_event": "APPLICATION_SUBMITTED",
    })

    logger.info(f"[WorkflowEngine] Initialized workflow for App {application_id}: {len(workflow_stages)} stages. Current: '{current_stage_name}'")

    # Auto-screen if first stage is AI Resume Screening
    try:
        if "resume" in current_stage_name.lower() or "screening" in current_stage_name.lower():
            await process_automatic_progression(application_id, current_stage_name)
    except Exception as e:
        logger.error(f"[WorkflowEngine] Error in initial auto-screening for App {application_id}: {e}")

    return {"workflow_stages": workflow_stages, "current_stage": current_stage_name}


async def advance_workflow_stage(
    application_id: str,
    recruiter_id: str,
    recruiter_name: str,
    notes: str = "",
    target_stage_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Advances candidate to the next stage (or a specified target stage).
    - Marks current stage Completed
    - Activates next stage
    - Appends timeline event
    - Creates candidate notification
    - Updates MongoDB atomically
    """
    db = get_database()
    app_doc = await db["applications"].find_one({"_id": ObjectId(application_id)})
    if not app_doc:
        raise ValueError(f"Application {application_id} not found.")

    workflow_stages: List[Dict] = app_doc.get("workflow_stages", [])
    if not workflow_stages or not isinstance(workflow_stages, list) or len(workflow_stages) == 0:
        logger.info(f"[WorkflowEngine] App {application_id} missing workflow_stages. Auto-initializing now...")
        workflow_stages = await ensure_workflow_initialized(app_doc)

    current_stage_name = app_doc.get("current_stage") or (workflow_stages[0]["stage_name"] if workflow_stages else "AI Resume Screening")
    candidate_id = app_doc["candidate_id"]
    job_id = app_doc["job_id"]
    company_id = app_doc.get("company_id", "")
    job_title = app_doc.get("job_title", "Position")

    if not workflow_stages:
        raise ValueError("Failed to initialize workflow stages for application.")

    # Find current stage index
    cur_idx = next((i for i, s in enumerate(workflow_stages) if s["stage_name"] == current_stage_name), 0)

    # Determine target index
    if target_stage_name:
        tgt_idx = next((i for i, s in enumerate(workflow_stages) if s["stage_name"] == target_stage_name), -1)
        if tgt_idx == -1:
            raise ValueError(f"Target stage '{target_stage_name}' not found in workflow.")
    else:
        tgt_idx = cur_idx + 1

    now_iso = datetime.now(timezone.utc).isoformat()

    new_stage_name = ""
    new_status = "Offer Released"

    if tgt_idx < len(workflow_stages):
        new_stage_name = workflow_stages[tgt_idx]["stage_name"]
        new_status = "In Progress"
        if new_stage_name == "Offer":
            new_status = "Offer Stage"
    else:
        new_stage_name = "Selected"
        new_status = "Selected"

    # Explicitly set status for every stage: before target = Completed, at target = Active, after target = Pending
    for idx, stg in enumerate(workflow_stages):
        if idx < tgt_idx:
            stg["status"] = "Completed"
            stg["execution_status"] = "Completed"
            if idx == cur_idx:
                stg["completed_at"] = now_iso
                stg["recruiter_decision"] = "Approved"
                if notes:
                    stg["recruiter_notes"] = notes
        elif idx == tgt_idx:
            stg["status"] = "Active"
            stg["execution_status"] = "Not Started"
            stg["started_at"] = now_iso
        else:
            stg["status"] = "Pending"
            stg["execution_status"] = "Not Started"

    # Build timeline event and audit entry
    timeline_event = make_timeline_event(
        f"STAGE_APPROVED_{current_stage_name.upper().replace(' ', '_')}",
        f"'{current_stage_name}' approved by {recruiter_name}. Moving to '{new_stage_name}'.",
        recruiter_name,
        {"from_stage": current_stage_name, "to_stage": new_stage_name}
    )
    audit_entry = make_audit_entry(
        application_id, candidate_id, recruiter_id, company_id, job_id,
        current_stage_name, "STAGE_ADVANCED", "Active", "Completed", recruiter_name
    )

    # Atomic MongoDB update
    await db["applications"].update_one(
        {"_id": ObjectId(application_id)},
        {
            "$set": {
                "workflow_stages": workflow_stages,
                "current_stage": new_stage_name,
                "current_stage_status": "Active" if tgt_idx < len(workflow_stages) else "Completed",
                "status": new_status,
                "updated_at": datetime.now(timezone.utc),
            },
            "$push": {
                "timeline": timeline_event,
                "audit_log": audit_entry,
            }
        }
    )

    # Candidate notification
    await insert_notification({
        "user_id": candidate_id,
        "type": "HIRING_WORKFLOW",
        "category": "Hiring Workflow",
        "priority": "High",
        "title": f"Stage Update: {new_stage_name}",
        "message": f"Congratulations! Your application for '{job_title}' has advanced to the '{new_stage_name}' stage.",
        "action_type": "VIEW_APPLICATION",
        "action_payload": {"application_id": application_id},
        "source_module": "workflow_engine",
        "source_event": "STAGE_ADVANCED",
    })

    logger.info(f"[WorkflowEngine] App {application_id}: Stage advanced from '{current_stage_name}' → '{new_stage_name}'")

    # Auto-archive if selected
    if new_stage_name == "Selected":
        await archive_application(application_id, "Selected", recruiter_name, notes)

    return {
        "previous_stage": current_stage_name,
        "current_stage": new_stage_name,
        "status": new_status,
        "workflow_stages": workflow_stages,
    }


async def reject_application(
    application_id: str,
    recruiter_id: str,
    recruiter_name: str,
    reason: str = "",
) -> Dict[str, Any]:
    """
    Rejects candidate application.
    - Sets current stage to Rejected
    - Sets application status to Rejected
    - Appends timeline event
    - Creates candidate notification
    - Archives to hiring_history
    """
    db = get_database()
    app_doc = await db["applications"].find_one({"_id": ObjectId(application_id)})
    if not app_doc:
        raise ValueError(f"Application {application_id} not found.")

    candidate_id = app_doc["candidate_id"]
    job_id = app_doc["job_id"]
    company_id = app_doc.get("company_id", "")
    current_stage = app_doc.get("current_stage", "")
    job_title = app_doc.get("job_title", "Position")
    now_iso = datetime.now(timezone.utc).isoformat()

    workflow_stages: List[Dict] = app_doc.get("workflow_stages", [])
    for s in workflow_stages:
        if s["stage_name"] == current_stage:
            s["status"] = "Rejected"
            s["recruiter_decision"] = "Rejected"
            s["completed_at"] = now_iso
            if reason:
                s["recruiter_notes"] = reason

    timeline_event = make_timeline_event(
        "APPLICATION_REJECTED",
        f"Application rejected at '{current_stage}' stage by {recruiter_name}." + (f" Reason: {reason}" if reason else ""),
        recruiter_name,
        {"stage": current_stage, "reason": reason}
    )
    audit_entry = make_audit_entry(
        application_id, candidate_id, recruiter_id, company_id, job_id,
        current_stage, "APPLICATION_REJECTED", "Active", "Rejected", recruiter_name, reason
    )

    await db["applications"].update_one(
        {"_id": ObjectId(application_id)},
        {
            "$set": {
                "workflow_stages": workflow_stages,
                "current_stage": "Rejected",
                "current_stage_status": "Rejected",
                "status": "Rejected",
                "updated_at": datetime.now(timezone.utc),
            },
            "$push": {
                "timeline": timeline_event,
                "audit_log": audit_entry,
            }
        }
    )

    # Candidate notification
    await insert_notification({
        "user_id": candidate_id,
        "type": "HIRING_WORKFLOW",
        "category": "Hiring Workflow",
        "priority": "Medium",
        "title": "Application Status Update",
        "message": f"We appreciate your interest in '{job_title}'. After careful consideration, we have decided not to move forward with your application at this time.",
        "action_type": "VIEW_APPLICATION",
        "action_payload": {"application_id": application_id},
        "source_module": "workflow_engine",
        "source_event": "APPLICATION_REJECTED",
    })

    logger.info(f"[WorkflowEngine] App {application_id} rejected at stage '{current_stage}' by {recruiter_name}")

    # Archive to hiring history
    await archive_application(application_id, "Rejected", recruiter_name, reason)

    return {"status": "Rejected", "current_stage": "Rejected"}


async def skip_stage(
    application_id: str,
    stage_name: str,
    recruiter_id: str,
    recruiter_name: str,
    reason: str = "",
) -> Dict[str, Any]:
    """
    Marks a stage as Skipped and activates the next stage.
    """
    db = get_database()
    app_doc = await db["applications"].find_one({"_id": ObjectId(application_id)})
    if not app_doc:
        raise ValueError(f"Application {application_id} not found.")

    workflow_stages: List[Dict] = app_doc.get("workflow_stages", [])
    now_iso = datetime.now(timezone.utc).isoformat()

    skipped_idx = next((i for i, s in enumerate(workflow_stages) if s["stage_name"] == stage_name), -1)
    if skipped_idx == -1:
        raise ValueError(f"Stage '{stage_name}' not found.")

    workflow_stages[skipped_idx]["status"] = "Skipped"
    workflow_stages[skipped_idx]["execution_status"] = "Skipped"
    workflow_stages[skipped_idx]["completed_at"] = now_iso

    next_stage_name = ""
    if skipped_idx + 1 < len(workflow_stages):
        workflow_stages[skipped_idx + 1]["status"] = "Active"
        workflow_stages[skipped_idx + 1]["execution_status"] = "Not Started"
        workflow_stages[skipped_idx + 1]["started_at"] = now_iso
        next_stage_name = workflow_stages[skipped_idx + 1]["stage_name"]

    timeline_event = make_timeline_event(
        "STAGE_SKIPPED",
        f"Stage '{stage_name}' skipped by {recruiter_name}." + (f" Reason: {reason}" if reason else ""),
        recruiter_name
    )
    audit_entry = make_audit_entry(
        application_id, app_doc["candidate_id"], recruiter_id,
        app_doc.get("company_id", ""), app_doc["job_id"],
        stage_name, "STAGE_SKIPPED", "Pending", "Skipped", recruiter_name, reason
    )

    await db["applications"].update_one(
        {"_id": ObjectId(application_id)},
        {
            "$set": {
                "workflow_stages": workflow_stages,
                "current_stage": next_stage_name or stage_name,
                "updated_at": datetime.now(timezone.utc),
            },
            "$push": {"timeline": timeline_event, "audit_log": audit_entry}
        }
    )

    return {"skipped_stage": stage_name, "current_stage": next_stage_name}


async def save_execution_result(
    application_id: str,
    stage_name: str,
    engine_type: str,
    result_payload: Dict[str, Any],
    performed_by: str,
    execution_status: str = "Submitted",
) -> Dict[str, Any]:
    """
    Saves stage execution result to db.stage_executions and updates workflow stage status.
    Called by all execution engines (Assessment, Interview, Portfolio, Offer) when candidate submits.
    """
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Upsert execution record
    exec_doc = {
        "application_id": application_id,
        "stage_name": stage_name,
        "engine_type": engine_type,
        "execution_status": execution_status,
        "result_payload": result_payload,
        "performed_by": performed_by,
        "submitted_at": now_iso,
        "updated_at": now_iso,
    }
    await db["stage_executions"].update_one(
        {"application_id": application_id, "stage_name": stage_name},
        {"$set": exec_doc},
        upsert=True
    )

    # Update workflow stage execution_status
    app_doc = await db["applications"].find_one({"_id": ObjectId(application_id)})
    if app_doc:
        workflow_stages = app_doc.get("workflow_stages", [])
        for s in workflow_stages:
            if s["stage_name"] == stage_name:
                s["execution_status"] = execution_status
                s["execution_result"] = result_payload
                break

        timeline_event = make_timeline_event(
            f"STAGE_SUBMITTED_{stage_name.upper().replace(' ', '_')}",
            f"Candidate submitted '{stage_name}' execution ({engine_type}).",
            performed_by,
        )

        await db["applications"].update_one(
            {"_id": ObjectId(application_id)},
            {
                "$set": {
                    "workflow_stages": workflow_stages,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$push": {"timeline": timeline_event}
            }
        )

        # Notify recruiter
        recruiter_id = app_doc.get("recruiter_id", "")
        if recruiter_id:
            await insert_notification({
                "user_id": recruiter_id,
                "type": "APPLICATIONS",
                "category": "Applications",
                "priority": "High",
                "title": f"Stage Submission: {stage_name}",
                "message": f"Candidate has submitted the '{stage_name}' stage. Review the result in Recruitment Studio.",
                "action_type": "OPEN_STUDIO",
                "action_payload": {"application_id": application_id},
                "source_module": "workflow_engine",
                "source_event": "STAGE_SUBMITTED",
            })

    # Trigger Automatic Stage Progression Engine
    try:
        prog_res = await process_automatic_progression(application_id, stage_name, result_payload)
        exec_doc["auto_progression"] = prog_res
    except Exception as e:
        logger.error(f"[AutoProgression] Error evaluating stage '{stage_name}' for App {application_id}: {e}")

    return exec_doc


MANUAL_STAGES = {
    "Manual Resume Review",
    "Technical Interview",
    "HR Round",
    "HR Interview",
    "Portfolio Review",
    "Offer",
}


async def process_automatic_progression(
    application_id: str,
    stage_name: str,
    result_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Automatic Stage Progression Engine.
    Reads stage configuration rules (passing_score, minimum_match_score, minimum_interview_score,
    auto_advance, auto_reject, recruiter_approval_required, weights).
    - If Manual stage or recruiter_approval_required is True -> Skip auto progression, wait for recruiter review.
    - If AI Resume Screening:
      - Reads candidate match score.
      - If score >= minimum_match_score and auto_advance is True -> Auto Advances.
      - Else if score < auto_reject_threshold and auto_reject is True -> Auto Rejects.
    - If Technical Assessment:
      - Reads overall_score from result_payload.
      - If overall_score >= passing_score (default 70) and auto_advance is True -> Auto Advances.
      - Else if overall_score < passing_score and auto_reject is True -> Auto Rejects.
    - If AI Interview:
      - Calculates weighted interview score: (comm_weight * comm_score) + (tech_weight * tech_score) + (conf_weight * conf_score)
      - If final_score >= minimum_interview_score (default 80) and auto_advance is True -> Auto Advances.
      - Else if final_score < minimum_interview_score and auto_reject is True -> Auto Rejects.
    """
    db = get_database()
    app_doc = await db["applications"].find_one({"_id": ObjectId(application_id)})
    if not app_doc:
        return {"auto_action": "NONE", "reason": "Application not found."}

    workflow_stages: List[Dict] = app_doc.get("workflow_stages", [])
    stage_obj = next((s for s in workflow_stages if s.get("stage_name") == stage_name), None)
    if not stage_obj:
        return {"auto_action": "NONE", "reason": f"Stage '{stage_name}' not found."}

    config = stage_obj.get("configuration", {}) or {}
    evaluation_mode = stage_obj.get("evaluation_mode", "AI")
    stage_type = stage_obj.get("stage_type", "AI")

    # Rule 1: Manual Stages and recruiter_approval_required ALWAYS require human decision
    is_manual = (
        stage_name in MANUAL_STAGES
        or stage_type == "Manual"
        or evaluation_mode == "Manual"
        or config.get("recruiter_approval_required") is True
    )
    if is_manual:
        logger.info(f"[AutoProgression] Stage '{stage_name}' is Manual / Recruiter Approval Required. Skipping auto-progression.")
        return {"auto_action": "NONE", "reason": "Manual stage requires recruiter decision."}

    auto_advance = config.get("auto_advance", True)
    auto_reject = config.get("auto_reject", True)

    system_actor = "System (Auto-Progression Engine)"
    recruiter_id = app_doc.get("recruiter_id", "system")

    # ─── EVALUATION RULE 1: AI RESUME SCREENING ────────────────────────────────
    if "resume" in stage_name.lower() or "screening" in stage_name.lower():
        ml_analysis = app_doc.get("ml_analysis") or app_doc.get("ai_match") or {}
        match_score = ml_analysis.get("overall_match_score") or (result_payload.get("match_score", 75) if result_payload else 75)
        min_match = config.get("minimum_match_score", config.get("auto_shortlist_threshold", 75))
        rej_threshold = config.get("auto_reject_threshold", 45)

        if match_score >= min_match and auto_advance:
            res = await advance_workflow_stage(
                application_id=application_id,
                recruiter_id=recruiter_id,
                recruiter_name=system_actor,
                notes=f"Auto-Advanced: AI Match Score ({match_score}%) >= Configured Threshold ({min_match}%).",
            )
            return {"auto_action": "ADVANCED", "score": match_score, "threshold": min_match, "result": res}

        elif match_score < rej_threshold and auto_reject:
            res = await reject_application(
                application_id=application_id,
                recruiter_id=recruiter_id,
                recruiter_name=system_actor,
                reason=f"Auto-Rejected: AI Match Score ({match_score}%) < Rejection Threshold ({rej_threshold}%).",
            )
            return {"auto_action": "REJECTED", "score": match_score, "threshold": rej_threshold, "result": res}

    # ─── EVALUATION RULE 2: TECHNICAL ASSESSMENT ──────────────────────────────
    elif "assessment" in stage_name.lower() or "coding" in stage_name.lower():
        if not result_payload:
            exec_rec = await db["stage_executions"].find_one({"application_id": application_id, "stage_name": stage_name})
            result_payload = exec_rec.get("result_payload", {}) if exec_rec else {}

        overall_score = result_payload.get("overall_score", result_payload.get("percentage", 0))
        passing_score = config.get("passing_score", 70)
        pass_status = result_payload.get("pass_status", result_payload.get("result", ""))

        if pass_status == "TERMINATED_FOR_INTEGRITY_VIOLATION" or pass_status == "FAILED":
            res = await reject_application(
                application_id=application_id,
                recruiter_id=recruiter_id,
                recruiter_name=system_actor,
                reason=f"Auto-Rejected: Assessment failed or terminated for integrity violation ({pass_status}).",
            )
            return {"auto_action": "REJECTED", "score": overall_score, "threshold": passing_score, "result": res}

        if overall_score >= passing_score and auto_advance:
            res = await advance_workflow_stage(
                application_id=application_id,
                recruiter_id=recruiter_id,
                recruiter_name=system_actor,
                notes=f"Auto-Advanced: Candidate Assessment Score ({overall_score}%) >= Passing Score ({passing_score}%).",
            )
            return {"auto_action": "ADVANCED", "score": overall_score, "threshold": passing_score, "result": res}

        elif overall_score < passing_score and auto_reject:
            res = await reject_application(
                application_id=application_id,
                recruiter_id=recruiter_id,
                recruiter_name=system_actor,
                reason=f"Auto-Rejected: Candidate Assessment Score ({overall_score}%) < Passing Score ({passing_score}%).",
            )
            return {"auto_action": "REJECTED", "score": overall_score, "threshold": passing_score, "result": res}

    # ─── EVALUATION RULE 3: AI INTERVIEW ─────────────────────────────────────
    elif "interview" in stage_name.lower() and ("ai" in stage_name.lower() or stage_type == "AI"):
        if not result_payload:
            exec_rec = await db["stage_executions"].find_one({"application_id": application_id, "stage_name": stage_name})
            result_payload = exec_rec.get("result_payload", {}) if exec_rec else {}

        comm_weight = config.get("communication_weight", 0.3)
        tech_weight = config.get("technical_weight", 0.5)
        conf_weight = config.get("confidence_weight", 0.2)

        comm_score = result_payload.get("communication_score", 85)
        tech_score = result_payload.get("technical_accuracy", 85)
        conf_score = result_payload.get("confidence_score", 85)

        weighted_score = round((comm_score * comm_weight) + (tech_score * tech_weight) + (conf_score * conf_weight), 1)
        min_interview_score = config.get("minimum_interview_score", config.get("passing_score", 80))

        if weighted_score >= min_interview_score and auto_advance:
            res = await advance_workflow_stage(
                application_id=application_id,
                recruiter_id=recruiter_id,
                recruiter_name=system_actor,
                notes=f"Auto-Advanced: AI Interview Score ({weighted_score}%) >= Minimum Score ({min_interview_score}%).",
            )
            return {"auto_action": "ADVANCED", "score": weighted_score, "threshold": min_interview_score, "result": res}

        elif weighted_score < min_interview_score and auto_reject:
            res = await reject_application(
                application_id=application_id,
                recruiter_id=recruiter_id,
                recruiter_name=system_actor,
                reason=f"Auto-Rejected: AI Interview Score ({weighted_score}%) < Minimum Score ({min_interview_score}%).",
            )
            return {"auto_action": "REJECTED", "score": weighted_score, "threshold": min_interview_score, "result": res}

    return {"auto_action": "NONE", "reason": "No auto progression rule triggered."}


async def archive_application(
    application_id: str,
    final_decision: str,
    decided_by: str,
    reason: str = "",
) -> None:
    """
    Archives application to db.hiring_history with full timeline, audit log, and stage results.
    """
    db = get_database()

    try:
        app_doc = await db["applications"].find_one({"_id": ObjectId(application_id)})
    except Exception:
        app_doc = None

    if not app_doc:
        logger.warning(f"[WorkflowEngine] Could not archive App {application_id}: not found.")
        return

    # Fetch stage executions
    executions_cursor = db["stage_executions"].find({"application_id": application_id})
    stage_results = []
    async for ex in executions_cursor:
        ex["_id"] = str(ex["_id"])
        stage_results.append(ex)

    history_doc = {
        "application_id": application_id,
        "candidate_id": app_doc["candidate_id"],
        "recruiter_id": app_doc.get("recruiter_id", ""),
        "company_id": app_doc.get("company_id", ""),
        "job_id": app_doc["job_id"],
        "job_title": app_doc.get("job_title", ""),
        "final_decision": final_decision,
        "decided_by": decided_by,
        "reason": reason,
        "timeline": app_doc.get("timeline", []),
        "audit_log": app_doc.get("audit_log", []),
        "workflow_stages": app_doc.get("workflow_stages", []),
        "stage_results": stage_results,
        "archived_at": datetime.now(timezone.utc).isoformat(),
    }

    await db["hiring_history"].update_one(
        {"application_id": application_id},
        {"$set": history_doc},
        upsert=True
    )

    logger.info(f"[WorkflowEngine] App {application_id} archived to hiring_history as '{final_decision}'.")


async def ensure_workflow_initialized(app_doc: dict) -> List[Dict[str, Any]]:
    """
    If an application document does not have workflow_stages populated,
    reads the job's hiring_workflow and initializes workflow stages on the fly.
    """
    workflow_stages = app_doc.get("workflow_stages", [])
    if workflow_stages and isinstance(workflow_stages, list) and len(workflow_stages) > 0:
        return workflow_stages

    application_id = str(app_doc.get("id") or app_doc.get("_id"))
    job_id = app_doc.get("job_id", "")
    candidate_id = app_doc.get("candidate_id", "")
    recruiter_id = app_doc.get("recruiter_id", "")
    company_id = app_doc.get("company_id", "")
    job_title = app_doc.get("job_title", "Position")
    company_name = app_doc.get("company_name", "Company")

    from app.database.job_db import get_job_workflow
    job_wf = await get_job_workflow(job_id) if job_id else []

    init_res = await init_application_workflow(
        application_id=application_id,
        candidate_id=candidate_id,
        recruiter_id=recruiter_id,
        company_id=company_id,
        job_id=job_id,
        job_title=job_title,
        company_name=company_name,
        job_workflow=job_wf,
    )
    return init_res.get("workflow_stages", [])


def compute_application_backend_state(app_doc: dict, workflow_stages: list) -> dict:
    status_overall = str(app_doc.get("status") or "").strip()
    c_stage = str(app_doc.get("current_stage") or "").strip()
    c_status = str(app_doc.get("current_stage_status") or "").strip()

    is_rejected = status_overall.lower() == "rejected" or c_stage.lower() == "rejected" or c_status.lower() == "rejected"
    is_withdrawn = status_overall.lower() == "withdrawn" or c_stage.lower() == "withdrawn" or c_status.lower() == "withdrawn"
    is_selected = status_overall.lower() in ["selected", "hired"] or c_stage.lower() in ["selected", "hired"]

    if is_rejected:
        app_status = "Rejected"
        cur_stage = "Rejected"
        can_continue = False
        action_label = None
        badge_variant = "danger"
        banner = "Application Decision: Not Selected / Rejected by Recruiter. Thank you for your time."
    elif is_withdrawn:
        app_status = "Withdrawn"
        cur_stage = "Withdrawn"
        can_continue = False
        action_label = None
        badge_variant = "danger"
        banner = "Application Withdrawn by Candidate."
    elif is_selected:
        app_status = "Selected"
        cur_stage = "Selected"
        can_continue = False
        action_label = "Offer Accepted"
        badge_variant = "success"
        banner = "Congratulations! Application Selected / Candidate Joined."
    else:
        cur_stage = c_stage or (workflow_stages[0]["stage_name"] if workflow_stages else "AI Resume Screening")
        active_stg = next((s for s in workflow_stages if s.get("stage_name", "").lower().strip() == cur_stage.lower().strip()), None)
        
        engine_type = active_stg.get("engine_type") if active_stg else "Resume Engine"
        eval_mode = active_stg.get("evaluation_mode", "AI") if active_stg else "AI"
        exec_status = active_stg.get("execution_status", "Not Started") if active_stg else "Not Started"

        if engine_type == "Assessment Engine":
            if exec_status in ["Submitted", "Completed"]:
                app_status = "Waiting for Recruiter"
                can_continue = False
                action_label = "Assessment Completed"
                badge_variant = "warning"
                banner = f"Assessment Submitted. Awaiting Recruiter Review ({cur_stage})."
            else:
                app_status = "Waiting for Candidate"
                can_continue = True
                action_label = f"Continue {cur_stage}"
                badge_variant = "warning"
                banner = f"Active Stage: Candidate Action Required ({cur_stage})."
        elif engine_type == "Interview Engine":
            if "ai interview" in cur_stage.lower() or cur_stage.lower() == "ai interview":
                if exec_status in ["Submitted", "Completed"]:
                    app_status = "Waiting for Recruiter"
                    can_continue = False
                    action_label = "Interview Submitted"
                    badge_variant = "warning"
                    banner = f"AI Interview Completed. Awaiting Recruiter Review ({cur_stage})."
                else:
                    app_status = "Waiting for Candidate"
                    can_continue = True
                    action_label = f"Start {cur_stage}"
                    badge_variant = "warning"
                    banner = f"Active Stage: Candidate Action Required ({cur_stage})."
            else:
                app_status = "Waiting for Recruiter"
                can_continue = False
                action_label = "Scheduled Interview"
                badge_variant = "primary"
                banner = f"Scheduled Interview in Progress ({cur_stage})."
        elif engine_type == "Offer Engine":
            if exec_status == "Offer Sent" or status_overall == "Offer Sent":
                app_status = "Offer Sent"
            app_status = "Offer Extended"
            can_continue = True
            action_label = "View Offer Letter"
            badge_variant = "success"
            banner = "Official Offer Extended! Review & Respond."
        elif engine_type == "Portfolio Engine":
            app_status = "Waiting for Candidate"
            can_continue = True
            action_label = "Submit Portfolio"
            badge_variant = "warning"
            banner = f"Active Stage: Portfolio Submission Required ({cur_stage})."
        else:
            app_status = "Waiting for Recruiter"
            can_continue = False
            action_label = None
            badge_variant = "primary"
            banner = f"Candidate Profile Under Review ({cur_stage})."

    return {
        "application_status": app_status,
        "current_stage": cur_stage,
        "can_continue": can_continue,
        "action_button_label": action_label,
        "is_rejected": is_rejected,
        "is_selected": is_selected,
        "is_withdrawn": is_withdrawn,
        "badge_variant": badge_variant,
        "status_banner": banner,
    }


async def get_application_workflow_state(application_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns full workflow state for an application including live stage statuses.
    Auto-initializes workflow stages if missing. Single source of truth for candidate & recruiter portals.
    """
    db = get_database()
    try:
        app_doc = await db["applications"].find_one({"_id": ObjectId(application_id)})
    except Exception:
        app_doc = None

    if not app_doc:
        return None

    app_doc["id"] = str(app_doc["_id"])
    app_doc["_id"] = str(app_doc["_id"])
    app_doc["application_id"] = str(app_doc["_id"])

    # Ensure workflow stages exist
    workflow_stages = app_doc.get("workflow_stages", [])
    if not workflow_stages or not isinstance(workflow_stages, list) or len(workflow_stages) == 0:
        workflow_stages = await ensure_workflow_initialized(app_doc)

    # Compute backend single source of truth state
    backend_state = compute_application_backend_state(app_doc, workflow_stages)
    app_doc["application_status"] = backend_state["application_status"]
    app_doc["status"] = backend_state["application_status"]
    app_doc["current_stage"] = backend_state["current_stage"]
    app_doc["candidate_actions"] = backend_state

    # Dynamically normalize stage statuses relative to current_stage
    if backend_state["is_rejected"]:
        for s in workflow_stages:
            if s.get("status") in ["Active", "In Progress", "Pending"]:
                s["status"] = "Rejected"
                s["execution_status"] = "Rejected"
    elif backend_state["is_withdrawn"]:
        for s in workflow_stages:
            if s.get("status") in ["Active", "In Progress", "Pending"]:
                s["status"] = "Withdrawn"
                s["execution_status"] = "Withdrawn"
    elif backend_state["is_selected"]:
        for s in workflow_stages:
            s["status"] = "Completed"
            s["execution_status"] = "Completed"
    else:
        cur_stage = backend_state["current_stage"]
        cur_idx = -1
        for idx, s in enumerate(workflow_stages):
            if s.get("stage_name", "").lower().strip() == cur_stage.lower().strip():
                cur_idx = idx
                break

        if cur_idx != -1:
            for idx, s in enumerate(workflow_stages):
                if idx < cur_idx:
                    s["status"] = "Completed"
                elif idx == cur_idx:
                    s["status"] = "Active"
                else:
                    s["status"] = "Pending"

    # Attach stage execution results
    for stage in workflow_stages:
        exec_rec = await db["stage_executions"].find_one({
            "application_id": application_id,
            "stage_name": stage["stage_name"]
        })
        if exec_rec:
            exec_rec["_id"] = str(exec_rec["_id"])
            stage["execution_result"] = exec_rec.get("result_payload", exec_rec.get("execution_result"))
            stage["execution_status"] = exec_rec.get("execution_status", stage.get("execution_status", "Not Started"))

    # Fetch candidate user info for real name & email from database
    cand_id = app_doc.get("candidate_id")
    if cand_id:
        cand_user = None
        try:
            cand_user = await db["users"].find_one({"_id": ObjectId(cand_id)})
        except Exception:
            pass
        if not cand_user:
            try:
                cand_user = await db["users"].find_one({"_id": cand_id})
            except Exception:
                pass
        if not cand_user:
            try:
                cand_user = await db["candidates"].find_one({"_id": ObjectId(cand_id)})
            except Exception:
                pass
        if cand_user:
            app_doc["candidate_name"] = cand_user.get("full_name") or cand_user.get("name") or app_doc.get("candidate_name") or "Applied Candidate"
            app_doc["candidate_email"] = cand_user.get("email") or app_doc.get("candidate_email") or app_doc.get("email") or ""

    app_doc["workflow_stages"] = workflow_stages
    app_doc["updated_at"] = app_doc.get("updated_at", datetime.now(timezone.utc)).isoformat() if isinstance(app_doc.get("updated_at"), datetime) else str(app_doc.get("updated_at", ""))
    return app_doc
