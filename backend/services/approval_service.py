from models.approval import ApprovalDecision
from models.ticket import TicketInvestigation


# ============================================================
# APPROVE INVESTIGATION
# ============================================================

def approve_investigation(
    investigation: TicketInvestigation,
    reviewer: str,
    comment: str | None = None
) -> TicketInvestigation:

    investigation.approval = ApprovalDecision(
        status="approved",
        reviewer=reviewer,
        comment=comment
    )

    return investigation


# ============================================================
# REJECT INVESTIGATION
# ============================================================

def reject_investigation(
    investigation: TicketInvestigation,
    reviewer: str,
    comment: str | None = None
) -> TicketInvestigation:

    investigation.approval = ApprovalDecision(
        status="rejected",
        reviewer=reviewer,
        comment=comment
    )

    return investigation


# ============================================================
# REQUEST MORE INVESTIGATION
# ============================================================

def request_more_investigation(
    investigation: TicketInvestigation,
    reviewer: str,
    comment: str | None = None
) -> TicketInvestigation:

    investigation.approval = ApprovalDecision(
        status="needs_more_investigation",
        reviewer=reviewer,
        comment=comment
    )

    return investigation