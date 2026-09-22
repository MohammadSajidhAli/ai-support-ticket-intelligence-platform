from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import json
import time
import os
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.database import (
    engine,
    get_db,
    Base
)

from models.ticket import (
    TicketCreate,
    TicketDB,
    TicketInvestigation
)

from models.approval import ApprovalDecision
from models.evaluation import InvestigationEvaluationDB

from services.agent_service import investigate_ticket
from services.rag_service import analyze_ticket_with_rag

from services.approval_service import (
    approve_investigation,
    reject_investigation,
    request_more_investigation
)

from services.resolution_service import execute_resolution

from services.ticket_service import (
    save_approval,
    save_resolution
)

from services.evaluation_service import (
    evaluate_investigation,
    record_investigation_failure
)

from auth.routes import router as auth_router
from auth.dependencies import (
    get_current_user,
    require_roles
)

from models.user import UserDB


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Support & Ticket Intelligence Platform",
    version="1.0.0"
)


# ============================================================
# AUTH ROUTES
# ============================================================

app.include_router(auth_router)


# ============================================================
# CORS
# ============================================================

frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# REQUEST MODELS
# ============================================================

class ApprovalRequest(BaseModel):
    """
    Approval/rejection request.

    The reviewer is intentionally NOT accepted from the
    frontend. The backend derives the reviewer from the
    authenticated JWT user.
    """

    comment: Optional[str] = None


# ============================================================
# INVESTIGATION PERSISTENCE
# ============================================================

def save_investigation(
    ticket: TicketDB,
    investigation: TicketInvestigation,
    db: Session
):
    """
    Persist the complete investigation inside the ticket.
    """

    ticket.investigation_data = json.dumps(
        investigation.model_dump()
    )

    db.commit()
    db.refresh(ticket)


def load_investigation(
    ticket: TicketDB
):
    """
    Load a previously persisted investigation.
    """

    if not ticket.investigation_data:
        return None

    try:
        return TicketInvestigation.model_validate(
            json.loads(ticket.investigation_data)
        )

    except Exception:
        return None


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "AI Support Platform is running"
    }


# ============================================================
# HEALTH
# PUBLIC
# ============================================================

@app.get("/health")
def health(
    db: Session = Depends(get_db)
):

    try:

        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "services": {
                "api": "healthy",
                "database": "healthy"
            }
        }

    except Exception as e:

        return {
            "status": "degraded",
            "services": {
                "api": "healthy",
                "database": "unhealthy"
            },
            "error": str(e)
        }


# ============================================================
# CREATE TICKET
# PUBLIC
# ============================================================

@app.post("/tickets")
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # STEP 1 — RAG + LLM ANALYSIS
    # --------------------------------------------------------

    rag_result = analyze_ticket_with_rag(
        customer=ticket.customer,
        issue=ticket.issue
    )

    analysis = rag_result["analysis"]
    sources = rag_result["sources"]

    # --------------------------------------------------------
    # STEP 2 — SERIALIZE LISTS
    # --------------------------------------------------------

    recommended_actions = json.dumps(
        analysis.recommended_actions
    )

    knowledge_sources = json.dumps(
        sources
    )

    # --------------------------------------------------------
    # STEP 3 — CREATE DATABASE RECORD
    # --------------------------------------------------------

    new_ticket = TicketDB(
        customer=ticket.customer,
        issue=ticket.issue,
        priority=ticket.priority,
        status="open",

        ai_category=analysis.category,
        ai_priority=analysis.priority,
        ai_summary=analysis.summary,
        ai_sentiment=analysis.sentiment,
        ai_root_cause=analysis.root_cause,

        ai_recommended_actions=recommended_actions,
        knowledge_sources=knowledge_sources
    )

    db.add(new_ticket)

    db.commit()

    db.refresh(new_ticket)

    # --------------------------------------------------------
    # STEP 4 — RESPONSE
    # --------------------------------------------------------

    return {

        "id": new_ticket.id,

        "customer": new_ticket.customer,

        "issue": new_ticket.issue,

        "priority": new_ticket.priority,

        "status": new_ticket.status,

        "ai_analysis": {

            "category": new_ticket.ai_category,

            "priority": new_ticket.ai_priority,

            "summary": new_ticket.ai_summary,

            "sentiment": new_ticket.ai_sentiment,

            "root_cause": new_ticket.ai_root_cause,

            "recommended_actions": (
                json.loads(
                    new_ticket.ai_recommended_actions
                )
            )
        },

        "knowledge_sources": (
            json.loads(
                new_ticket.knowledge_sources
            )
        )
    }


# ============================================================
# GET ALL TICKETS
# AUTHENTICATED USERS
# ============================================================

@app.get("/tickets")
def get_tickets(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):

    tickets = (
        db.query(TicketDB)
        .all()
    )

    return [

        {

            "id": ticket.id,

            "customer": ticket.customer,

            "issue": ticket.issue,

            "priority": ticket.priority,

            "status": ticket.status,

            "ai_analysis": {

                "category":
                    ticket.ai_category,

                "priority":
                    ticket.ai_priority,

                "summary":
                    ticket.ai_summary,

                "sentiment":
                    ticket.ai_sentiment,

                "root_cause":
                    ticket.ai_root_cause,

                "recommended_actions":
                    (
                        json.loads(
                            ticket.ai_recommended_actions
                        )
                        if ticket.ai_recommended_actions
                        else []
                    )
            },

            "knowledge_sources":
                (
                    json.loads(
                        ticket.knowledge_sources
                    )
                    if ticket.knowledge_sources
                    else []
                ),

            "approval": {

                "status":
                    ticket.approval_status,

                "reviewer":
                    ticket.approved_by,

                "comment":
                    ticket.approval_comment
            },

            "resolution": {

                "status":
                    ticket.resolution_status,

                "action":
                    ticket.resolution_action,

                "message":
                    ticket.resolution_message
            },

            "investigation":
                (
                    json.loads(
                        ticket.investigation_data
                    )
                    if ticket.investigation_data
                    else None
                )
        }

        for ticket in tickets
    ]


# ============================================================
# GET SINGLE TICKET
# AUTHENTICATED USERS
# ============================================================

@app.get("/tickets/{ticket_id}")
def get_single_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):

    ticket = (
        db.query(TicketDB)
        .filter(
            TicketDB.id == ticket_id
        )
        .first()
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return {

        "id": ticket.id,

        "customer": ticket.customer,

        "issue": ticket.issue,

        "priority": ticket.priority,

        "status": ticket.status,

        "ai_analysis": {

            "category":
                ticket.ai_category,

            "priority":
                ticket.ai_priority,

            "summary":
                ticket.ai_summary,

            "sentiment":
                ticket.ai_sentiment,

            "root_cause":
                ticket.ai_root_cause,

            "recommended_actions":
                (
                    json.loads(
                        ticket.ai_recommended_actions
                    )
                    if ticket.ai_recommended_actions
                    else []
                )
        },

        "knowledge_sources":
            (
                json.loads(
                    ticket.knowledge_sources
                )
                if ticket.knowledge_sources
                else []
            ),

        "approval": {

            "status":
                ticket.approval_status,

            "reviewer":
                ticket.approved_by,

            "comment":
                ticket.approval_comment
        },

        "resolution": {

            "status":
                ticket.resolution_status,

            "action":
                ticket.resolution_action,

            "message":
                ticket.resolution_message
        },

        "investigation":
            (
                json.loads(
                    ticket.investigation_data
                )
                if ticket.investigation_data
                else None
            )
    }


# ============================================================
# INVESTIGATE TICKET
# ADMIN + SUPPORT AGENT ONLY
# ============================================================

@app.post("/tickets/{ticket_id}/investigate")
def investigate_ticket_endpoint(
    ticket_id: int,
    db: Session = Depends(get_db),

    current_user: UserDB = Depends(
        require_roles(
            "admin",
            "support_agent"
        )
    )
):

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # STEP 1 — FIND TICKET
    # --------------------------------------------------------

    ticket = (
        db.query(TicketDB)
        .filter(
            TicketDB.id == ticket_id
        )
        .first()
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # --------------------------------------------------------
    # STEP 2 — RUN AI INVESTIGATION
    # --------------------------------------------------------

    try:

        investigation = investigate_ticket(
            ticket_id=ticket_id
        )

        # ----------------------------------------------------
        # STEP 3 — SAVE INVESTIGATION
        # ----------------------------------------------------

        save_investigation(
            ticket=ticket,
            investigation=investigation,
            db=db
        )

        # ----------------------------------------------------
        # STEP 4 — CALCULATE DURATION
        # ----------------------------------------------------

        duration_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        # ----------------------------------------------------
        # STEP 5 — EVALUATE
        # ----------------------------------------------------

        try:

            evaluate_investigation(
                ticket_id=ticket_id,
                investigation=investigation,
                duration_ms=duration_ms
            )

        except Exception as evaluation_error:

            print(
                f"[EVALUATION ERROR] "
                f"Ticket {ticket_id}: "
                f"{evaluation_error}"
            )

        # ----------------------------------------------------
        # STEP 6 — RETURN
        # ----------------------------------------------------

        return {

            "ticket_id":
                ticket_id,

            "investigation":
                investigation.model_dump(),

            "duration_ms":
                round(
                    duration_ms,
                    2
                ),

            "status":
                "success"
        }

    # --------------------------------------------------------
    # INVESTIGATION FAILURE
    # --------------------------------------------------------

    except Exception as e:

        duration_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        print(
            f"[INVESTIGATION ERROR] "
            f"Ticket {ticket_id}: {e}"
        )

        try:

            record_investigation_failure(
                ticket_id=ticket_id,
                duration_ms=duration_ms,
                error_message=str(e)
            )

        except Exception as evaluation_error:

            print(
                f"[FAILURE EVALUATION ERROR] "
                f"Ticket {ticket_id}: "
                f"{evaluation_error}"
            )

        raise HTTPException(
            status_code=500,
            detail={
                "message":
                    "AI investigation failed.",

                "ticket_id":
                    ticket_id,

                "error":
                    str(e),

                "duration_ms":
                    round(
                        duration_ms,
                        2
                    )
            }
        )


# ============================================================
# APPROVE INVESTIGATION
# ADMIN + SUPPORT AGENT ONLY
# ============================================================

@app.post("/tickets/{ticket_id}/approve")
def approve_ticket(
    ticket_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),

    current_user: UserDB = Depends(
        require_roles(
            "admin",
            "support_agent"
        )
    )
):

    ticket = (
        db.query(TicketDB)
        .filter(
            TicketDB.id == ticket_id
        )
        .first()
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    investigation = load_investigation(
        ticket
    )

    if investigation is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Investigation must be completed "
                "before approval."
            )
        )

    # IMPORTANT:
    # Reviewer is taken from the authenticated user,
    # NOT from the frontend request.

    reviewer = current_user.username

    investigation = approve_investigation(
        investigation=investigation,
        reviewer=reviewer,
        comment=request.comment
    )

    save_investigation(
        ticket=ticket,
        investigation=investigation,
        db=db
    )

    save_approval(
        ticket_id=ticket_id,
        approval_status=(
            investigation.approval.status
        ),
        approved_by=(
            investigation.approval.reviewer
        ),
        approval_comment=(
            investigation.approval.comment
        )
    )

    return {

        "ticket_id":
            ticket_id,

        "message":
            "Investigation approved",

        "investigation":
            investigation.model_dump(),

        "approval":
            investigation.approval.model_dump()
    }


# ============================================================
# REJECT INVESTIGATION
# ADMIN + SUPPORT AGENT ONLY
# ============================================================

@app.post("/tickets/{ticket_id}/reject")
def reject_ticket(
    ticket_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),

    current_user: UserDB = Depends(
        require_roles(
            "admin",
            "support_agent"
        )
    )
):

    ticket = (
        db.query(TicketDB)
        .filter(
            TicketDB.id == ticket_id
        )
        .first()
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    investigation = load_investigation(
        ticket
    )

    if investigation is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Investigation must be completed "
                "before rejection."
            )
        )

    # IMPORTANT:
    # Reviewer is taken from the authenticated user.

    reviewer = current_user.username

    investigation = reject_investigation(
        investigation=investigation,
        reviewer=reviewer,
        comment=request.comment
    )

    save_investigation(
        ticket=ticket,
        investigation=investigation,
        db=db
    )

    save_approval(
        ticket_id=ticket_id,
        approval_status=(
            investigation.approval.status
        ),
        approved_by=(
            investigation.approval.reviewer
        ),
        approval_comment=(
            investigation.approval.comment
        )
    )

    return {

        "ticket_id":
            ticket_id,

        "message":
            "Investigation rejected",

        "investigation":
            investigation.model_dump(),

        "approval":
            investigation.approval.model_dump()
    }


# ============================================================
# REQUEST MORE INVESTIGATION
# ADMIN + SUPPORT AGENT ONLY
# ============================================================

@app.post("/tickets/{ticket_id}/investigate-more")
def investigate_more(
    ticket_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),

    current_user: UserDB = Depends(
        require_roles(
            "admin",
            "support_agent"
        )
    )
):

    ticket = (
        db.query(TicketDB)
        .filter(
            TicketDB.id == ticket_id
        )
        .first()
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    investigation = load_investigation(
        ticket
    )

    if investigation is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Investigation must be completed "
                "before requesting more investigation."
            )
        )

    # IMPORTANT:
    # Reviewer is taken from the authenticated user.

    reviewer = current_user.username

    investigation = request_more_investigation(
        investigation=investigation,
        reviewer=reviewer,
        comment=request.comment
    )

    save_investigation(
        ticket=ticket,
        investigation=investigation,
        db=db
    )

    save_approval(
        ticket_id=ticket_id,
        approval_status=(
            investigation.approval.status
        ),
        approved_by=(
            investigation.approval.reviewer
        ),
        approval_comment=(
            investigation.approval.comment
        )
    )

    return {

        "ticket_id":
            ticket_id,

        "message":
            "More investigation requested",

        "investigation":
            investigation.model_dump(),

        "approval":
            investigation.approval.model_dump()
    }


# ============================================================
# EXECUTE RESOLUTION
# ADMIN + SUPPORT AGENT ONLY
# ============================================================

@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),

    current_user: UserDB = Depends(
        require_roles(
            "admin",
            "support_agent"
        )
    )
):

    # --------------------------------------------------------
    # STEP 1 — FIND TICKET
    # --------------------------------------------------------

    ticket = (
        db.query(TicketDB)
        .filter(
            TicketDB.id == ticket_id
        )
        .first()
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # --------------------------------------------------------
    # STEP 2 — APPROVAL SAFETY CHECK
    # --------------------------------------------------------

    if ticket.approval_status != "approved":

        raise HTTPException(
            status_code=403,
            detail=(
                "Resolution cannot be executed because "
                "the investigation has not been approved."
            )
        )

    # --------------------------------------------------------
    # STEP 3 — LOAD INVESTIGATION
    # --------------------------------------------------------

    investigation = load_investigation(
        ticket
    )

    if investigation is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Investigation must be completed "
                "before resolution."
            )
        )

    # --------------------------------------------------------
    # STEP 4 — RESTORE APPROVAL
    # --------------------------------------------------------

    investigation.approval = ApprovalDecision(
        status="approved",
        reviewer=ticket.approved_by,
        comment=ticket.approval_comment
    )

    # --------------------------------------------------------
    # STEP 5 — EXECUTE RESOLUTION
    # --------------------------------------------------------

    try:

        result = execute_resolution(
            investigation
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Resolution execution failed.",
                "ticket_id": ticket_id,
                "error": str(e)
            }
        )

    # --------------------------------------------------------
    # STEP 6 — CHECK RESULT
    # --------------------------------------------------------

    if not result.success:

        save_resolution(
            ticket_id=ticket_id,

            resolution_action=result.action,

            resolution_status="failed",

            resolution_message=result.message
        )

        db.refresh(ticket)

        raise HTTPException(
            status_code=400,
            detail={
                "message": result.message,
                "ticket_id": ticket_id,
                "resolution": result.model_dump()
            }
        )

    # --------------------------------------------------------
    # STEP 7 — SAVE RESOLUTION
    # --------------------------------------------------------

    save_resolution(
        ticket_id=ticket_id,

        resolution_action=result.action,

        resolution_status="success",

        resolution_message=result.message
    )

    # --------------------------------------------------------
    # STEP 8 — MARK TICKET RESOLVED
    # --------------------------------------------------------

    ticket.status = "resolved"

    db.commit()
    db.refresh(ticket)

    # --------------------------------------------------------
    # STEP 9 — RESPONSE
    # --------------------------------------------------------

    return {

        "ticket_id": ticket_id,

        "status": ticket.status,

        "resolution": {

            "success":
                result.success,

            "action":
                result.action,

            "message":
                result.message
        },

        "approval": {

            "status":
                ticket.approval_status,

            "reviewer":
                ticket.approved_by,

            "comment":
                ticket.approval_comment
        }
    }


# ============================================================
# DASHBOARD / OBSERVABILITY METRICS
# AUTHENTICATED USERS
# ============================================================

@app.get("/dashboard/metrics")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):

    tickets = (
        db.query(TicketDB)
        .all()
    )

    evaluations = (
        db.query(
            InvestigationEvaluationDB
        )
        .all()
    )

    total_tickets = len(tickets)

    status_counts = {}

    for ticket in tickets:

        status = ticket.status or "unknown"

        status_counts[status] = (
            status_counts.get(status, 0) + 1
        )

    investigated_count = sum(
        1
        for ticket in tickets
        if ticket.investigation_data
    )

    approved_count = sum(
        1
        for ticket in tickets
        if ticket.approval_status == "approved"
    )

    rejected_count = sum(
        1
        for ticket in tickets
        if ticket.approval_status == "rejected"
    )

    evaluation_count = len(evaluations)

    if evaluations:

        average_duration = (
            sum(
                evaluation.duration_ms
                for evaluation in evaluations
            )
            / evaluation_count
        )

        average_confidence = (
            sum(
                evaluation.confidence
                for evaluation in evaluations
            )
            / evaluation_count
        )

        average_overall_score = (
            sum(
                evaluation.overall_score
                for evaluation in evaluations
            )
            / evaluation_count
        )

        successful_evaluations = sum(
            1
            for evaluation in evaluations
            if evaluation.status == "success"
        )

        success_rate = (
            successful_evaluations
            / evaluation_count
        )

    else:

        average_duration = 0
        average_confidence = 0
        average_overall_score = 0
        success_rate = 0

    return {

        "tickets": {

            "total":
                total_tickets,

            "investigated":
                investigated_count,

            "approved":
                approved_count,

            "rejected":
                rejected_count,

            "by_status":
                status_counts
        },

        "evaluation": {

            "count":
                evaluation_count,

            "average_duration_ms":
                round(
                    average_duration,
                    2
                ),

            "average_confidence":
                round(
                    average_confidence,
                    3
                ),

            "average_overall_score":
                round(
                    average_overall_score,
                    3
                ),

            "success_rate":
                round(
                    success_rate,
                    3
                )
        }
    }


# ============================================================
# GET TICKET EVALUATION
# AUTHENTICATED USERS
# ============================================================

@app.get("/tickets/{ticket_id}/evaluation")
def get_ticket_evaluation(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):

    evaluation = (
        db.query(
            InvestigationEvaluationDB
        )
        .filter(
            InvestigationEvaluationDB.ticket_id
            == ticket_id
        )
        .order_by(
            InvestigationEvaluationDB.id.desc()
        )
        .first()
    )

    if not evaluation:

        raise HTTPException(
            status_code=404,
            detail=(
                "No evaluation found for this ticket."
            )
        )

    return {

        "id":
            evaluation.id,

        "ticket_id":
            evaluation.ticket_id,

        "duration_ms":
            evaluation.duration_ms,

        "evidence_count":
            evaluation.evidence_count,

        "unique_source_count":
            evaluation.unique_source_count,

        "recommended_action_count":
            evaluation.recommended_action_count,

        "confidence":
            evaluation.confidence,

        "scores": {

            "evidence":
                evaluation.evidence_score,

            "source_diversity":
                evaluation.source_diversity_score,

            "actionability":
                evaluation.actionability_score,

            "completeness":
                evaluation.completeness_score,

            "overall":
                evaluation.overall_score
        },

        "status":
            evaluation.status,

        "error_message":
            evaluation.error_message,

        "created_at":
            evaluation.created_at
    }