from models.ticket import TicketInvestigation


# ============================================================
# RESOLUTION RESULT
# ============================================================

class ResolutionResult:

    def __init__(
        self,
        success: bool,
        action: str,
        message: str
    ):
        self.success = success
        self.action = action
        self.message = message

    def model_dump(self):

        return {
            "success": self.success,
            "action": self.action,
            "message": self.message
        }


# ============================================================
# EXECUTE RESOLUTION
# ============================================================

def execute_resolution(
    investigation: TicketInvestigation
) -> ResolutionResult:

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if investigation.approval.status != "approved":

        return ResolutionResult(

            success=False,

            action="none",

            message=(
                "Resolution cannot be executed because "
                "the investigation has not been approved."
            )
        )


    # --------------------------------------------------------
    # GET RECOMMENDED ACTIONS
    # --------------------------------------------------------

    actions = investigation.recommended_actions


    if not actions:

        return ResolutionResult(

            success=False,

            action="none",

            message=(
                "No recommended resolution is available."
            )
        )


    # --------------------------------------------------------
    # SIMULATED RESOLUTION
    # --------------------------------------------------------

    primary_action = actions[0]


    print()

    print(
        "[RESOLUTION] Executing approved action"
    )

    print(
        f"[RESOLUTION] Action: {primary_action}"
    )


    # --------------------------------------------------------
    # SIMULATE SUCCESS
    # --------------------------------------------------------

    return ResolutionResult(

        success=True,

        action=primary_action,

        message=(
            "Resolution executed successfully "
            "(simulation)."
        )
    )