from pydantic import BaseModel
from typing import Optional, Literal


class ApprovalDecision(BaseModel):
    status: Literal[
        "pending",
        "approved",
        "rejected",
        "needs_more_investigation"
    ] = "pending"

    reviewer: Optional[str] = None
    comment: Optional[str] = None