from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from datetime import datetime

from database.database import Base


class InvestigationEvaluationDB(Base):
    __tablename__ = "investigation_evaluations"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(Integer, nullable=False, index=True)

    duration_ms = Column(Float, nullable=False)

    evidence_count = Column(Integer, nullable=False)

    unique_source_count = Column(Integer, nullable=False)

    recommended_action_count = Column(Integer, nullable=False)

    confidence = Column(Float, nullable=False)

    evidence_score = Column(Float, nullable=False)

    source_diversity_score = Column(Float, nullable=False)

    actionability_score = Column(Float, nullable=False)

    completeness_score = Column(Float, nullable=False)

    overall_score = Column(Float, nullable=False)

    status = Column(String(50), nullable=False)

    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )