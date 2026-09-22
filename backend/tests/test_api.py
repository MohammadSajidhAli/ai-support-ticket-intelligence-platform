
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# pyrefly: ignore [missing-import]
import pytest

# Allow imports when pytest is run from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main
from models.ticket import TicketInvestigation, EvidenceItem


def make_investigation(
    confidence=0.85,
    approval_status="pending",
):
    investigation = TicketInvestigation(
        summary="API failures started after the latest deployment.",
        evidence=[
            EvidenceItem(
                type="logs",
                source="logs.txt",
                finding="Database connection pool exhausted."
            ),
            EvidenceItem(
                type="deployment",
                source="deployments.txt",
                finding="Latest deployment changed database configuration."
            ),
        ],
        root_cause_hypothesis=(
            "The latest deployment likely caused database "
            "connection pool exhaustion."
        ),
        confidence=confidence,
        recommended_actions=[
            "Roll back the latest deployment.",
            "Verify database connection settings.",
            "Monitor API error rate."
        ],
        sources=[
            "logs.txt",
            "deployments.txt"
        ],
    )

    # Keep the default approval state unless a test needs another one.
    investigation.approval.status = approval_status

    return investigation


# ============================================================
# BASIC ENDPOINTS
# ============================================================

def test_home():
    result = main.home()

    assert result["message"] == (
        "AI Support Platform is running"
    )


def test_health():
    db = MagicMock()

    # The updated health endpoint executes SELECT 1.
    db.execute.return_value = None

    result = main.health(db)

    assert result["status"] == "healthy"
    assert result["services"]["api"] == "healthy"
    assert result["services"]["database"] == "healthy"


# ============================================================
# INVESTIGATION
# ============================================================

def test_investigation_success(monkeypatch):
    investigation = make_investigation()

    ticket = SimpleNamespace(
        id=2,
        investigation_data=None
    )

    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = ticket

    monkeypatch.setattr(
        main,
        "investigate_ticket",
        lambda ticket_id: investigation
    )

    saved = {}

    def fake_save_investigation(ticket, investigation, db):
        saved["investigation"] = investigation

    monkeypatch.setattr(
        main,
        "save_investigation",
        fake_save_investigation
    )

    evaluation_called = {}

    def fake_evaluate_investigation(
        ticket_id,
        investigation,
        duration_ms
    ):
        evaluation_called["ticket_id"] = ticket_id
        evaluation_called["investigation"] = investigation
        evaluation_called["duration_ms"] = duration_ms

    monkeypatch.setattr(
        main,
        "evaluate_investigation",
        fake_evaluate_investigation
    )

    result = main.investigate_ticket_endpoint(
        ticket_id=2,
        db=db
    )

    assert result["ticket_id"] == 2
    assert result["status"] == "success"
    assert "investigation" in result
    assert result["investigation"]["confidence"] == 0.85

    assert saved["investigation"] is investigation
    assert evaluation_called["ticket_id"] == 2


def test_investigation_ticket_not_found():
    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(main.HTTPException) as exc:
        main.investigate_ticket_endpoint(
            ticket_id=999999,
            db=db
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Ticket not found"


def test_investigation_failure_is_recorded(monkeypatch):
    ticket = SimpleNamespace(
        id=2,
        investigation_data=None
    )

    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = ticket

    monkeypatch.setattr(
        main,
        "investigate_ticket",
        lambda ticket_id: (
            (_ for _ in ()).throw(
                RuntimeError("Ollama unavailable")
            )
        )
    )

    failure = {}

    def fake_record_failure(
        ticket_id,
        duration_ms,
        error_message
    ):
        failure["ticket_id"] = ticket_id
        failure["error_message"] = error_message
        failure["duration_ms"] = duration_ms

    monkeypatch.setattr(
        main,
        "record_investigation_failure",
        fake_record_failure
    )

    with pytest.raises(main.HTTPException) as exc:
        main.investigate_ticket_endpoint(
            ticket_id=2,
            db=db
        )

    assert exc.value.status_code == 500

    detail = exc.value.detail

    assert detail["message"] == "AI investigation failed."
    assert detail["ticket_id"] == 2
    assert detail["error"] == "Ollama unavailable"

    assert failure["ticket_id"] == 2
    assert failure["error_message"] == "Ollama unavailable"


def test_evaluation_failure_does_not_fail_investigation(
    monkeypatch
):
    investigation = make_investigation()

    ticket = SimpleNamespace(
        id=2,
        investigation_data=None
    )

    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = ticket

    monkeypatch.setattr(
        main,
        "investigate_ticket",
        lambda ticket_id: investigation
    )

    monkeypatch.setattr(
        main,
        "save_investigation",
        lambda ticket, investigation, db: None
    )

    monkeypatch.setattr(
        main,
        "evaluate_investigation",
        lambda **kwargs: (
            (_ for _ in ()).throw(
                RuntimeError("Evaluation DB unavailable")
            )
        )
    )

    result = main.investigate_ticket_endpoint(
        ticket_id=2,
        db=db
    )

    assert result["status"] == "success"


# ============================================================
# APPROVAL
# ============================================================

def test_approve_requires_investigation():
    ticket = SimpleNamespace(
        id=2,
        investigation_data=None
    )

    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = ticket

    request = main.ApprovalRequest(
        reviewer="Sajidh",
        comment="Evidence is sufficient"
    )

    with pytest.raises(main.HTTPException) as exc:
        main.approve_ticket(
            ticket_id=2,
            request=request,
            db=db
        )

    assert exc.value.status_code == 400


def test_reject_requires_investigation():
    ticket = SimpleNamespace(
        id=2,
        investigation_data=None
    )

    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = ticket

    request = main.ApprovalRequest(
        reviewer="Sajidh",
        comment="Evidence is insufficient"
    )

    with pytest.raises(main.HTTPException) as exc:
        main.reject_ticket(
            ticket_id=2,
            request=request,
            db=db
        )

    assert exc.value.status_code == 400


# ============================================================
# RESOLUTION SAFETY
# ============================================================

def test_resolution_requires_approval():
    ticket = SimpleNamespace(
        id=2,
        approval_status="pending"
    )

    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = ticket

    with pytest.raises(main.HTTPException) as exc:
        main.resolve_ticket(
            ticket_id=2,
            db=db
        )

    assert exc.value.status_code == 403


def test_resolution_requires_saved_investigation():
    ticket = SimpleNamespace(
        id=2,
        approval_status="approved",
        approved_by="Sajidh",
        approval_comment="Approved"
    )

    db = MagicMock()

    db.query.return_value.filter.return_value.first.return_value = ticket

    monkeypatch = pytest.MonkeyPatch()

    try:
        monkeypatch.setattr(
            main,
            "load_investigation",
            lambda ticket: None
        )

        with pytest.raises(main.HTTPException) as exc:
            main.resolve_ticket(
                ticket_id=2,
                db=db
            )

        assert exc.value.status_code == 400

    finally:
        monkeypatch.undo()


# ============================================================
# EVALUATION SERVICE
# ============================================================

def test_evaluation_scores_are_created(monkeypatch):
    from services import evaluation_service

    fake_db = MagicMock()

    monkeypatch.setattr(
        evaluation_service,
        "SessionLocal",
        lambda: fake_db
    )

    evaluation = evaluation_service.evaluate_investigation(
        ticket_id=2,
        investigation=make_investigation(),
        duration_ms=1250.5
    )

    created = fake_db.add.call_args.args[0]

    assert evaluation is created
    assert created.ticket_id == 2
    assert created.duration_ms == 1250.5
    assert created.evidence_count == 2
    assert created.unique_source_count == 2
    assert created.recommended_action_count == 3
    assert created.confidence == 0.85
    assert created.status == "success"

    assert 0 <= created.overall_score <= 1


def test_failure_evaluation_is_recorded(monkeypatch):
    from services import evaluation_service

    fake_db = MagicMock()

    monkeypatch.setattr(
        evaluation_service,
        "SessionLocal",
        lambda: fake_db
    )

    evaluation = (
        evaluation_service.record_investigation_failure(
            ticket_id=2,
            duration_ms=44.5,
            error_message="Ollama unavailable"
        )
    )

    created = fake_db.add.call_args.args[0]

    assert evaluation is created
    assert created.ticket_id == 2
    assert created.duration_ms == 44.5
    assert created.status == "failed"
    assert created.error_message == "Ollama unavailable"
    assert created.overall_score == 0.0
    assert created.confidence == 0.0


# ============================================================
# PERSISTENCE HELPERS
# ============================================================

def test_save_and_load_investigation(monkeypatch):
    investigation = make_investigation()

    ticket = SimpleNamespace(
        id=2,
        investigation_data=None
    )

    db = MagicMock()

    main.save_investigation(
        ticket=ticket,
        investigation=investigation,
        db=db
    )

    assert ticket.investigation_data is not None

    loaded = main.load_investigation(ticket)

    assert loaded is not None
    assert loaded.summary == investigation.summary
    assert loaded.confidence == investigation.confidence
    assert len(loaded.evidence) == 2


def test_load_investigation_returns_none_when_missing():
    ticket = SimpleNamespace(
        id=2,
        investigation_data=None
    )

    result = main.load_investigation(ticket)

    assert result is None


def test_load_investigation_returns_none_for_invalid_json():
    ticket = SimpleNamespace(
        id=2,
        investigation_data="{invalid-json"
    )

    result = main.load_investigation(ticket)

    assert result is None


# ============================================================
# EVALUATION API SHAPE
# ============================================================

def test_get_ticket_evaluation_not_found():
    db = MagicMock()

    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    with pytest.raises(main.HTTPException) as exc:
        main.get_ticket_evaluation(
            ticket_id=999999,
            db=db
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == (
        "No evaluation found for this ticket."
    )
