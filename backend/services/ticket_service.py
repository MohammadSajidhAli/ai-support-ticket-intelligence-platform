from database.database import SessionLocal

from models.ticket import TicketDB


# ============================================================
# GET TICKET
# ============================================================

def get_ticket_from_database(
    ticket_id: int
):

    db = SessionLocal()

    try:

        ticket = db.query(
            TicketDB
        ).filter(
            TicketDB.id == ticket_id
        ).first()

        return ticket

    finally:

        db.close()


# ============================================================
# SAVE APPROVAL
# ============================================================

def save_approval(
    ticket_id: int,
    approval_status: str,
    approved_by: str | None,
    approval_comment: str | None
):

    db = SessionLocal()

    try:

        ticket = db.query(
            TicketDB
        ).filter(
            TicketDB.id == ticket_id
        ).first()


        if ticket is None:

            raise ValueError(
                f"Ticket {ticket_id} not found"
            )


        ticket.approval_status = approval_status

        ticket.approved_by = approved_by

        ticket.approval_comment = approval_comment


        db.commit()

        db.refresh(ticket)

        return ticket

    finally:

        db.close()


# ============================================================
# SAVE RESOLUTION
# ============================================================

def save_resolution(
    ticket_id: int,
    resolution_action: str,
    resolution_status: str,
    resolution_message: str
):

    db = SessionLocal()

    try:

        ticket = db.query(
            TicketDB
        ).filter(
            TicketDB.id == ticket_id
        ).first()


        if ticket is None:

            raise ValueError(
                f"Ticket {ticket_id} not found"
            )


        ticket.resolution_action = (
            resolution_action
        )

        ticket.resolution_status = (
            resolution_status
        )

        ticket.resolution_message = (
            resolution_message
        )


        if resolution_status == "success":

            ticket.status = "resolved"


        db.commit()

        db.refresh(ticket)

        return ticket

    finally:

        db.close()