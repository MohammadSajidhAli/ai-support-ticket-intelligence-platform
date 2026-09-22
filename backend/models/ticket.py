from typing import Literal

from pydantic import BaseModel

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text
)

from database.database import Base

from models.approval import ApprovalDecision

# ============================================================
# CREATE TICKET REQUEST
# ============================================================

class TicketCreate(BaseModel):

    customer: str

    issue: str

    priority: str


# ============================================================
# AI TICKET ANALYSIS
# ============================================================

class TicketAnalysis(BaseModel):

    category: str

    priority: Literal[
        "low",
        "medium",
        "high",
        "critical"
    ]

    summary: str

    sentiment: Literal[
        "positive",
        "neutral",
        "negative",
        "urgent"
    ]

    root_cause: str

    recommended_actions: list[str]


class EvidenceItem(BaseModel):

    type: Literal[
        "ticket",
        "knowledge_base",
        "logs",
        "service_status",
        "deployment",
        "historical_ticket"
    ]

    source: str

    finding: str


class TicketInvestigation(BaseModel):

    summary: str

    evidence: list[EvidenceItem]

    root_cause_hypothesis: str

    confidence: float

    recommended_actions: list[str]

    sources: list[str]

    approval: ApprovalDecision = ApprovalDecision()
# ============================================================
# DATABASE MODEL
# ============================================================

class TicketDB(Base):

    __tablename__ = "tickets"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    customer = Column(
        String(255),
        nullable=False
    )


    issue = Column(
        Text,
        nullable=False
    )


    priority = Column(
        String(50),
        nullable=False
    )


    status = Column(
        String(50),
        default="open"
    )


    # --------------------------------------------------------
    # AI ANALYSIS
    # --------------------------------------------------------

    ai_category = Column(
        String(100)
    )


    ai_priority = Column(
        String(50)
    )


    ai_summary = Column(
        Text
    )


    ai_sentiment = Column(
        String(50)
    )


    ai_root_cause = Column(
        Text
    )


    ai_recommended_actions = Column(
        Text
    )


    # --------------------------------------------------------
    # RAG SOURCES
    # --------------------------------------------------------

    knowledge_sources = Column(
        Text
    )

        # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    approval_status = Column(
        String(50)
    )

    approved_by = Column(
        String(255)
    )

    approval_comment = Column(
        Text
    )


    # --------------------------------------------------------
    # RESOLUTION
    # --------------------------------------------------------

    resolution_action = Column(
        Text
    )

    resolution_status = Column(
        String(50)
    )

    resolution_message = Column(
        Text
    )

    investigation_data = Column(Text)