from services.approval_service import approve_investigation

from services.resolution_service import (
    execute_resolution,
)

from services.ticket_service import (
    save_approval,
    save_resolution,
    get_ticket_from_database,
)


# ============================================================
# RESOLUTION TEST
# ============================================================

def test_resolution_flow(sample_investigation):

    # ========================================================
    # STEP 1 — USE SAMPLE AI INVESTIGATION
    # ========================================================

    investigation = sample_investigation

    print()
    print("=" * 70)
    print("INITIAL INVESTIGATION")
    print("=" * 70)
    print(investigation.model_dump())


    # ========================================================
    # STEP 2 — HUMAN APPROVAL
    # ========================================================

    investigation = approve_investigation(
        investigation=investigation,
        reviewer="Sajidh",
        comment="Evidence is sufficient",
    )

    print()
    print("=" * 70)
    print("APPROVAL")
    print("=" * 70)
    print(investigation.approval.model_dump())

    assert investigation.approval.status == "approved"


    # ========================================================
    # STEP 3 — SAVE APPROVAL TO DATABASE
    # ========================================================

    save_approval(
        ticket_id=1,
        approval_status=investigation.approval.status,
        approved_by=investigation.approval.reviewer,
        approval_comment=investigation.approval.comment,
    )

    print()
    print("[DATABASE] Approval saved")


    # ========================================================
    # STEP 4 — EXECUTE RESOLUTION
    # ========================================================

    resolution = execute_resolution(
        investigation
    )

    print()
    print("=" * 70)
    print("RESOLUTION")
    print("=" * 70)
    print(resolution.model_dump())


    # ========================================================
    # STEP 5 — SAVE RESOLUTION
    # ========================================================

    if resolution.success:

        save_resolution(
            ticket_id=1,
            resolution_action=resolution.action,
            resolution_status="success",
            resolution_message=resolution.message,
        )

    else:

        save_resolution(
            ticket_id=1,
            resolution_action=resolution.action,
            resolution_status="failed",
            resolution_message=resolution.message,
        )

    print()
    print("[DATABASE] Resolution saved")


    # ========================================================
    # STEP 6 — VERIFY DATABASE
    # ========================================================

    ticket = get_ticket_from_database(
        ticket_id=1
    )

    print()
    print("=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)

    print("Ticket ID:", ticket.id)
    print("Status:", ticket.status)
    print("Approval Status:", ticket.approval_status)
    print("Approved By:", ticket.approved_by)
    print("Approval Comment:", ticket.approval_comment)
    print("Resolution Status:", ticket.resolution_status)
    print("Resolution Action:", ticket.resolution_action)
    print("Resolution Message:", ticket.resolution_message)


    # ========================================================
    # ASSERTIONS
    # ========================================================

    assert ticket.id == 1
    assert ticket.approval_status == "approved"
    assert ticket.approved_by == "Sajidh"
    assert ticket.approval_comment == "Evidence is sufficient"

    assert ticket.resolution_status in [
        "success",
        "failed",
    ]