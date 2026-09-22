import sys
from pathlib import Path

import pytest


# ============================================================
# Make backend importable
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# Import investigation models
# ============================================================

from models.approval import ApprovalDecision
from models.ticket import TicketInvestigation, EvidenceItem


# ============================================================
# Sample investigation fixture
# ============================================================

@pytest.fixture
def sample_investigation():
    """
    Deterministic investigation used by approval/resolution tests.

    IMPORTANT:
    This does NOT call Ollama.
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
                ),
            ),

            EvidenceItem(
                type="knowledge_base",
                source="api_errors.txt",
                finding=(
                    "500 errors can be caused by "
                    "database connection failures."
                ),
            ),

            EvidenceItem(
                type="logs",
                source="logs.txt",
                finding=(
                    "API error rate increased significantly "
                    "after deployment."
                ),
            ),

            EvidenceItem(
                type="service_status",
                source="service_status.txt",
                finding=(
                    "Database is unhealthy and API is degraded."
                ),
            ),

            EvidenceItem(
                type="deployment",
                source="deployments.txt",
                finding=(
                    "Database connection configuration changed "
                    "in the latest deployment."
                ),
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