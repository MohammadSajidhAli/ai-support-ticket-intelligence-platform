from services.approval_service import (
    approve_investigation,
    reject_investigation,
    request_more_investigation,
)


# ============================================================
# APPROVAL TEST
# ============================================================

def test_approve_investigation(sample_investigation):

    investigation = sample_investigation

    approved = approve_investigation(
        investigation=investigation,
        reviewer="Sajidh",
        comment="Evidence is sufficient",
    )

    print()
    print("=" * 70)
    print("AFTER APPROVAL")
    print("=" * 70)
    print(approved.model_dump())

    assert approved.approval.status == "approved"
    assert approved.approval.reviewer == "Sajidh"
    assert approved.approval.comment == "Evidence is sufficient"