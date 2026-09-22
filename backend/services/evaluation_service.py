from database.database import SessionLocal
from models.evaluation import InvestigationEvaluationDB


def evaluate_investigation(
    ticket_id: int,
    investigation,
    duration_ms: float
):
    evidence = investigation.evidence or []
    sources = investigation.sources or []
    recommended_actions = investigation.recommended_actions or []

    evidence_count = len(evidence)
    unique_sources = len(set(sources))
    action_count = len(recommended_actions)
    confidence = float(investigation.confidence or 0)

    evidence_score = min(evidence_count / 8, 1.0)
    source_diversity_score = min(unique_sources / 5, 1.0)
    actionability_score = min(action_count / 3, 1.0)

    completeness_items = [
        bool(investigation.summary),
        bool(investigation.root_cause_hypothesis),
        investigation.confidence is not None,
        unique_sources > 0,
        action_count > 0
    ]

    completeness_score = (
        sum(completeness_items) / len(completeness_items)
    )

    overall_score = (
        evidence_score * 0.30
        + source_diversity_score * 0.20
        + actionability_score * 0.20
        + completeness_score * 0.30
    )

    db = SessionLocal()

    try:
        evaluation = InvestigationEvaluationDB(
            ticket_id=ticket_id,
            duration_ms=duration_ms,
            evidence_count=evidence_count,
            unique_source_count=unique_sources,
            recommended_action_count=action_count,
            confidence=confidence,
            evidence_score=round(evidence_score, 3),
            source_diversity_score=round(source_diversity_score, 3),
            actionability_score=round(actionability_score, 3),
            completeness_score=round(completeness_score, 3),
            overall_score=round(overall_score, 3),
            status="success",
            error_message=None
        )

        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        return evaluation

    finally:
        db.close()


def record_investigation_failure(
    ticket_id: int,
    duration_ms: float,
    error_message: str
):
    db = SessionLocal()

    try:
        evaluation = InvestigationEvaluationDB(
            ticket_id=ticket_id,
            duration_ms=duration_ms,
            evidence_count=0,
            unique_source_count=0,
            recommended_action_count=0,
            confidence=0.0,
            evidence_score=0.0,
            source_diversity_score=0.0,
            actionability_score=0.0,
            completeness_score=0.0,
            overall_score=0.0,
            status="failed",
            error_message=str(error_message)
        )

        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        return evaluation

    finally:
        db.close()
