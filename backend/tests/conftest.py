import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ============================================================
# Make backend importable
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# Import application
# ============================================================

from main import app
from auth.dependencies import get_current_user


# ============================================================
# Import investigation models
# ============================================================

from models.approval import ApprovalDecision
from models.ticket import TicketInvestigation, EvidenceItem


# ============================================================
# Test authentication user
# ============================================================

class TestUser:
    id = 999
    username = "test_agent"
    email = "test@example.com"
    role = "support_agent"
    is_active = True


TEST_USER = TestUser()


# ============================================================
# App fixture
# ============================================================

@pytest.fixture
def app_instance():
    return app


# ============================================================
# Client fixture
# ============================================================

@pytest.fixture
def client():
    """
    Default behavior for existing API tests.

    Existing API tests don't send JWT tokens, so give them
    a fake authenticated support agent.
    """

    app.dependency_overrides[get_current_user] = (
        lambda: TEST_USER
    )

    with TestClient(app) as test_client:
        yield test_client

    # IMPORTANT:
    # Remove overrides after every test.
    app.dependency_overrides.clear()


# ============================================================
# Sample investigation fixture
# ============================================================

@pytest.fixture
def sample_investigation():
    """
    Deterministic investigation object for tests.

    IMPORTANT:
    This fixture does NOT call Ollama or investigate_ticket().
    Therefore pytest remains fast and does not depend on
    the live LLM.
    """

    return TicketInvestigation(
        summary=(
            "Production API is returning 500 errors "
            "after the latest deployment."
        ),

        evidence=[
            EvidenceItem(
                type="ticket",
                source="Ticket #1",
                finding=(
                    "Production API is returning 500 errors "
                    "after the latest deployment."
                )
            ),

            EvidenceItem(
                type="knowledge_base",
                source="api_errors.txt",
                finding=(
                    "500 errors can be caused by "
                    "database connection failures."
                )
            ),

            EvidenceItem(
                type="logs",
                source="logs.txt",
                finding=(
                    "API error rate increased significantly "
                    "after deployment."
                )
            ),

            EvidenceItem(
                type="service_status",
                source="service_status.txt",
                finding=(
                    "Database is unhealthy and API is degraded."
                )
            ),

            EvidenceItem(
                type="deployment",
                source="deployments.txt",
                finding=(
                    "Database connection configuration changed "
                    "in the latest deployment."
                )
            ),
        ],

        root_cause_hypothesis=(
            "The latest deployment introduced a database "
            "connection configuration issue causing API "
            "500 errors."
        ),

        confidence=0.8,

        recommended_actions=[
            "Review the database connection configuration.",
            "Compare the current deployment with the previous release.",
            "Verify database environment variables.",
            "Rollback the deployment if the configuration issue is confirmed.",
        ],

        sources=[
            "Ticket #1",
            "api_errors.txt",
            "logs.txt",
            "service_status.txt",
            "deployments.txt",
        ],

        approval=ApprovalDecision(
            status="pending"
        ),
    )