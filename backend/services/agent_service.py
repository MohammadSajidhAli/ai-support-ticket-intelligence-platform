import json
from typing import Any

import ollama

from models.ticket import (
    EvidenceItem,
    TicketInvestigation,
)

from models.approval import ApprovalDecision

from services.tools_service import (
    get_ticket,
    search_knowledge_base,
    search_similar_tickets,
    search_logs,
    get_service_status,
    get_deployment_info,
)


# ============================================================
# CONFIGURATION
# ============================================================

LLM_MODEL = "llama3.2"

# Maximum backend evidence tool executions.
MAX_TOOL_CALLS = 8

REQUIRED_INVESTIGATION_TOOLS = {
    "get_ticket",
    "search_knowledge_base",
    "search_similar_tickets",
    "search_logs",
    "get_service_status",
    "get_deployment_info",
}


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "get_ticket",
            "description": (
                "Retrieve the raw customer support ticket "
                "from the database using its ticket ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "The ID of the ticket.",
                    }
                },
                "required": ["ticket_id"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search internal company documentation "
                "for troubleshooting procedures, known "
                "technical issues, and possible causes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Technical issue to investigate.",
                    }
                },
                "required": ["query"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_similar_tickets",
            "description": (
                "Search historical support tickets for "
                "similar customer issues."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "Description of the current issue.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results.",
                    },
                    "exclude_ticket_id": {
                        "type": "integer",
                        "description": "Ticket ID to exclude.",
                    },
                },
                "required": ["issue"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": (
                "Search operational application logs "
                "for evidence related to the incident."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Terms related to the incident.",
                    }
                },
                "required": [],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_service_status",
            "description": (
                "Retrieve the current status of production "
                "services and infrastructure."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_deployment_info",
            "description": (
                "Retrieve recent deployment information "
                "including release changes and observations."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# ============================================================
# SERIALIZATION
# ============================================================

def serialize_tool_result(result: Any) -> str:

    try:
        return json.dumps(
            result,
            indent=2,
            default=str,
        )

    except Exception:
        return str(result)


# ============================================================
# TOOL CALL EXTRACTION
# ============================================================

def get_tool_calls(message: Any) -> list:

    if message is None:
        return []

    if isinstance(message, dict):

        return message.get(
            "tool_calls",
            [],
        ) or []

    return getattr(
        message,
        "tool_calls",
        [],
    ) or []


def extract_tool_call(tool_call: Any):

    if isinstance(tool_call, dict):

        function = tool_call.get(
            "function",
            {},
        )

        name = function.get(
            "name",
        )

        arguments = function.get(
            "arguments",
            {},
        )

    else:

        function = getattr(
            tool_call,
            "function",
            None,
        )

        if function is None:
            raise ValueError(
                "Invalid tool call returned by LLM."
            )

        name = getattr(
            function,
            "name",
            None,
        )

        arguments = getattr(
            function,
            "arguments",
            {},
        )

    if arguments is None:
        arguments = {}

    if isinstance(arguments, str):

        try:
            arguments = json.loads(arguments)

        except json.JSONDecodeError:

            raise ValueError(
                f"Invalid JSON arguments for tool '{name}'."
            )

    if not isinstance(arguments, dict):

        raise ValueError(
            f"Tool arguments for '{name}' must be an object."
        )

    if not name:

        raise ValueError(
            "Tool name is missing."
        )

    return name, arguments


# ============================================================
# TOOL EXECUTOR
# ============================================================

def execute_tool(
    tool_name: str,
    arguments: dict,
) -> Any:

    if not isinstance(arguments, dict):
        arguments = {}

    # --------------------------------------------------------
    # GET TICKET
    # --------------------------------------------------------

    if tool_name == "get_ticket":

        if "ticket_id" not in arguments:

            raise ValueError(
                "get_ticket requires ticket_id."
            )

        return get_ticket(
            ticket_id=int(
                arguments["ticket_id"]
            )
        )

    # --------------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------------

    if tool_name == "search_knowledge_base":

        return search_knowledge_base(
            query=str(
                arguments.get(
                    "query",
                    "",
                )
            )
        )

    # --------------------------------------------------------
    # SIMILAR TICKETS
    # --------------------------------------------------------

    if tool_name == "search_similar_tickets":

        issue = arguments.get(
            "issue",
            "",
        )

        limit = arguments.get(
            "limit",
            5,
        )

        exclude_ticket_id = arguments.get(
            "exclude_ticket_id",
        )

        return search_similar_tickets(
            issue=str(issue),
            limit=int(limit),
            exclude_ticket_id=(
                int(exclude_ticket_id)
                if exclude_ticket_id is not None
                else None
            ),
        )

    # --------------------------------------------------------
    # LOGS
    # --------------------------------------------------------

    if tool_name == "search_logs":

        return search_logs(
            query=str(
                arguments.get(
                    "query",
                    "",
                )
            )
        )

    # --------------------------------------------------------
    # SERVICE STATUS
    # --------------------------------------------------------

    if tool_name == "get_service_status":

        return get_service_status()

    # --------------------------------------------------------
    # DEPLOYMENT
    # --------------------------------------------------------

    if tool_name == "get_deployment_info":

        return get_deployment_info()

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )


# ============================================================
# BUILD VERIFIED EVIDENCE
# ============================================================

def build_verified_evidence(
    ticket: dict | None,
    knowledge_results: list,
    similar_tickets: list,
    logs: list,
    service_status: Any,
    deployment_info: Any,
) -> list[EvidenceItem]:

    verified_evidence = []

    # --------------------------------------------------------
    # CURRENT TICKET
    # --------------------------------------------------------

    if ticket:

        verified_evidence.append(

            EvidenceItem(
                type="ticket",
                source=f"Ticket #{ticket['id']}",
                finding=(
                    f"Customer {ticket['customer']} "
                    f"reported: {ticket['issue']}. "
                    f"Priority: {ticket['priority']}. "
                    f"Status: {ticket['status']}."
                ),
            )
        )

    # --------------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------------

    for item in knowledge_results or []:

        if not isinstance(item, dict):
            continue

        source = item.get(
            "source",
            "knowledge_base",
        )

        content = item.get(
            "content",
            "",
        )

        verified_evidence.append(

            EvidenceItem(
                type="knowledge_base",
                source=str(source),
                finding=str(content),
            )
        )

    # --------------------------------------------------------
    # LOGS
    # --------------------------------------------------------

    for log in logs or []:

        verified_evidence.append(

            EvidenceItem(
                type="logs",
                source="logs.txt",
                finding=str(log),
            )
        )

    # --------------------------------------------------------
    # SERVICE STATUS
    # --------------------------------------------------------

    if service_status:

        verified_evidence.append(

            EvidenceItem(
                type="service_status",
                source="service_status.txt",
                finding=str(service_status),
            )
        )

    # --------------------------------------------------------
    # DEPLOYMENT
    # --------------------------------------------------------

    if deployment_info:

        verified_evidence.append(

            EvidenceItem(
                type="deployment",
                source="deployments.txt",
                finding=str(deployment_info),
            )
        )

    # --------------------------------------------------------
    # HISTORICAL TICKETS
    # --------------------------------------------------------

    for historical_ticket in similar_tickets or []:

        if not isinstance(
            historical_ticket,
            dict,
        ):
            continue

        ticket_number = historical_ticket.get(
            "ticket_id",
        )

        similarity = historical_ticket.get(
            "similarity",
        )

        issue = historical_ticket.get(
            "issue",
            "",
        )

        verified_evidence.append(

            EvidenceItem(
                type="historical_ticket",
                source=f"Ticket #{ticket_number}",
                finding=(
                    f"Similarity: {similarity}. "
                    f"{issue}"
                ),
            )
        )

    return verified_evidence


# ============================================================
# REQUIRED EVIDENCE
# ============================================================

def get_missing_required_tools(
    completed_tools: set[str],
) -> set[str]:

    return (
        REQUIRED_INVESTIGATION_TOOLS
        - completed_tools
    )


# ============================================================
# FAST EVIDENCE COLLECTION
# ============================================================

def collect_required_evidence(
    ticket: dict,
    ticket_id: int,
) -> tuple[dict, dict]:

    """
    Collect all required evidence directly from backend tools.

    IMPORTANT:
    We intentionally do NOT call Ollama between every tool.

    This prevents the LLM from repeatedly selecting tools that
    have already been executed.

    Returns:
        completed_tools
        tool_results
    """

    completed_tools: set[str] = {
        "get_ticket"
    }

    tool_results: dict[str, list] = {}

    # --------------------------------------------------------
    # TICKET
    # --------------------------------------------------------

    tool_results["get_ticket"] = [

        {
            "arguments": {
                "ticket_id": ticket_id,
            },
            "result": ticket,
        }
    ]

    issue = str(
        ticket.get(
            "issue",
            "",
        )
    )

    # --------------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------------

    print()
    print(
        "[AGENT] Collecting required evidence:"
    )

    print(
        "        search_knowledge_base"
    )

    knowledge_results = execute_tool(
        "search_knowledge_base",
        {
            "query": issue,
        },
    )

    completed_tools.add(
        "search_knowledge_base"
    )

    tool_results["search_knowledge_base"] = [

        {
            "arguments": {
                "query": issue,
            },
            "result": knowledge_results,
        }
    ]

    print(
        "[AGENT] search_knowledge_base completed"
    )

    # --------------------------------------------------------
    # LOGS
    # --------------------------------------------------------

    print(
        "        search_logs"
    )

    logs = execute_tool(
        "search_logs",
        {
            "query": issue,
        },
    )

    completed_tools.add(
        "search_logs"
    )

    tool_results["search_logs"] = [

        {
            "arguments": {
                "query": issue,
            },
            "result": logs,
        }
    ]

    print(
        "[AGENT] search_logs completed"
    )

    # --------------------------------------------------------
    # SIMILAR TICKETS
    # --------------------------------------------------------

    print(
        "        search_similar_tickets"
    )

    similar_tickets = execute_tool(
        "search_similar_tickets",
        {
            "issue": issue,
            "limit": 5,
            "exclude_ticket_id": ticket_id,
        },
    )

    completed_tools.add(
        "search_similar_tickets"
    )

    tool_results["search_similar_tickets"] = [

        {
            "arguments": {
                "issue": issue,
                "limit": 5,
                "exclude_ticket_id": ticket_id,
            },
            "result": similar_tickets,
        }
    ]

    print(
        "[AGENT] search_similar_tickets completed"
    )

    # --------------------------------------------------------
    # SERVICE STATUS
    # --------------------------------------------------------

    print(
        "        get_service_status"
    )

    service_status = execute_tool(
        "get_service_status",
        {},
    )

    completed_tools.add(
        "get_service_status"
    )

    tool_results["get_service_status"] = [

        {
            "arguments": {},
            "result": service_status,
        }
    ]

    print(
        "[AGENT] get_service_status completed"
    )

    # --------------------------------------------------------
    # DEPLOYMENT
    # --------------------------------------------------------

    print(
        "        get_deployment_info"
    )

    deployment_info = execute_tool(
        "get_deployment_info",
        {},
    )

    completed_tools.add(
        "get_deployment_info"
    )

    tool_results["get_deployment_info"] = [

        {
            "arguments": {},
            "result": deployment_info,
        }
    ]

    print(
        "[AGENT] get_deployment_info completed"
    )

    print()
    print(
        "[AGENT] All required evidence collected."
    )

    print(
        "[AGENT] Proceeding to final reasoning."
    )

    return completed_tools, tool_results


# ============================================================
# INVESTIGATION AGENT
# ============================================================

def investigate_ticket(
    ticket_id: int,
) -> TicketInvestigation:

    print()
    print("=" * 70)
    print(
        f"AI AGENT STARTED — TICKET #{ticket_id}"
    )
    print("=" * 70)

    # ========================================================
    # STEP 1 — INITIAL LLM CALL
    # ========================================================

    initial_messages = [

        {
            "role": "system",
            "content": """
You are an AI production incident investigation agent.

You must begin an investigation by retrieving the support
ticket using get_ticket.

Do not invent facts.

Use backend evidence for the investigation.

After retrieving the ticket, the backend will collect the
required operational evidence.

Your final conclusion will be generated from verified backend
evidence only.
""",
        },

        {
            "role": "user",
            "content": (
                f"Investigate support ticket #{ticket_id}. "
                f"Start by retrieving the ticket."
            ),
        },
    ]

    print()
    print(
        "[AGENT] Initial reasoning..."
    )

    response = ollama.chat(

        model=LLM_MODEL,

        messages=initial_messages,

        tools=TOOLS,
    )

    message = response.get(
        "message",
        {},
    )

    tool_calls = get_tool_calls(
        message
    )

    # ========================================================
    # STEP 2 — RETRIEVE TICKET
    # ========================================================

    ticket = None

    if tool_calls:

        for tool_call in tool_calls:

            tool_name, arguments = extract_tool_call(
                tool_call
            )

            # We only need the ticket at this stage.
            if tool_name == "get_ticket":

                print()
                print(
                    "[AGENT] Tool selected: get_ticket"
                )

                print(
                    "[AGENT] Arguments: "
                    f"{json.dumps(arguments)}"
                )

                ticket = execute_tool(
                    tool_name,
                    arguments,
                )

                print()
                print(
                    "[AGENT] Tool completed: get_ticket"
                )

                print(
                    serialize_tool_result(
                        ticket
                    )
                )

                break

    # --------------------------------------------------------
    # Fallback if LLM did not call get_ticket correctly.
    # --------------------------------------------------------

    if ticket is None:

        print()
        print(
            "[GUARDRAIL] LLM did not retrieve ticket."
        )

        print(
            "[GUARDRAIL] Executing get_ticket."
        )

        ticket = execute_tool(
            "get_ticket",
            {
                "ticket_id": ticket_id,
            },
        )

        print(
            "[GUARDRAIL] get_ticket completed"
        )

    if not isinstance(
        ticket,
        dict,
    ):

        raise ValueError(
            "get_ticket returned invalid ticket data."
        )

    # ========================================================
    # STEP 3 — REQUIRED EVIDENCE COLLECTION
    # ========================================================

    completed_tools, tool_results = (
        collect_required_evidence(
            ticket=ticket,
            ticket_id=ticket_id,
        )
    )

    # ========================================================
    # STEP 4 — VERIFY REQUIRED EVIDENCE
    # ========================================================

    missing_tools = get_missing_required_tools(
        completed_tools
    )

    if missing_tools:

        raise ValueError(
            "Required evidence missing: "
            f"{sorted(missing_tools)}"
        )

    # ========================================================
    # STEP 5 — GET RESULTS
    # ========================================================

    def latest_result(
        tool_name: str,
    ):

        results = tool_results.get(
            tool_name,
            [],
        )

        if not results:
            return None

        return results[-1]["result"]

    knowledge_results = latest_result(
        "search_knowledge_base"
    )

    similar_tickets = latest_result(
        "search_similar_tickets"
    )

    logs = latest_result(
        "search_logs"
    )

    service_status = latest_result(
        "get_service_status"
    )

    deployment_info = latest_result(
        "get_deployment_info"
    )

    # ========================================================
    # NORMALIZE
    # ========================================================

    if knowledge_results is None:
        knowledge_results = []

    if similar_tickets is None:
        similar_tickets = []

    if logs is None:
        logs = []

    if service_status is None:
        service_status = ""

    if deployment_info is None:
        deployment_info = ""

    # ========================================================
    # STEP 6 — BUILD VERIFIED EVIDENCE
    # ========================================================

    verified_evidence = build_verified_evidence(

        ticket=ticket,

        knowledge_results=knowledge_results,

        similar_tickets=similar_tickets,

        logs=logs,

        service_status=service_status,

        deployment_info=deployment_info,
    )

    print()
    print(
        f"[AGENT] Verified evidence items: "
        f"{len(verified_evidence)}"
    )

    # ========================================================
    # STEP 7 — FINAL LLM REASONING
    # ========================================================

    evidence_text = json.dumps(

        [
            item.model_dump()
            for item in verified_evidence
        ],

        indent=2,

        default=str,
    )

    final_prompt = f"""
You are the final reasoning engine for a production
incident investigation system.

Your job is to determine the MOST SPECIFIC root-cause
hypothesis supported by the VERIFIED BACKEND EVIDENCE.

Analyze ONLY the evidence below.

VERIFIED EVIDENCE:

{evidence_text}

============================================================
REASONING REQUIREMENTS
============================================================

1. Separate the incident into:

   OBSERVED SYMPTOM
   TRIGGERING EVENT
   DIRECT EVIDENCE
   ROOT-CAUSE HYPOTHESIS
   SUPPORTING EVIDENCE

2. The customer ticket describes the symptom.
   Do NOT treat the ticket description as proof of root cause.

3. Prefer direct operational evidence over generic
   knowledge-base information.

4. Prefer evidence with a clear TIME relationship.

   Example:

   deployment
        ↓
   configuration change
        ↓
   infrastructure/database error
        ↓
   service degradation
        ↓
   customer-facing failure

5. If a deployment happened immediately before the incident,
   explicitly consider whether the deployment is related.

6. If deployment information identifies specific changes,
   mention those changes instead of saying only
   "deployment issue".

7. If logs identify a specific error, include that error.

8. If service status identifies a specific failure,
   include that failure.

9. If multiple pieces of evidence point to the same cause,
   connect them into ONE causal explanation.

10. Historical tickets are supporting context only.
    They must NOT override current operational evidence.

11. Knowledge-base documents provide technical context.
    They must NOT be treated as proof that a particular
    failure occurred.

12. Do NOT invent missing configuration values,
    error messages, infrastructure components,
    or events.

13. Do NOT give a generic root cause such as:
    - "deployment issue"
    - "configuration problem"
    - "server problem"
    - "database issue"
    unless the evidence cannot support anything more specific.

14. Be specific about WHAT changed, WHAT failed,
    and HOW that relates to the customer symptom.

15. Root cause remains a hypothesis unless directly proven.

16. Confidence must reflect the strength of the evidence.

    0.90 - 1.00:
    Multiple independent pieces of direct evidence strongly
    support the same explanation.

    0.70 - 0.89:
    Evidence strongly suggests the explanation but some
    uncertainty remains.

    0.50 - 0.69:
    Evidence suggests the explanation but important
    information is missing.

    Below 0.50:
    Evidence is insufficient or conflicting.

17. Recommended actions must directly address the
    identified root-cause hypothesis.

18. Do not recommend actions unrelated to the evidence.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

{{
    "summary": "Short description of the incident",

    "root_cause_hypothesis":
        "Specific evidence-grounded explanation of what
         most likely caused the incident",

    "confidence": 0.0,

    "recommended_actions": [
        "Action directly addressing the suspected cause",
        "Action to verify the suspected cause",
        "Recovery or mitigation action if supported"
    ]
}}
"""

    print()
    print(
        "[AGENT] Generating final investigation..."
    )

    final_response = ollama.chat(

        model=LLM_MODEL,

        messages=[

            {
                "role": "system",
                "content": (
                    "You are a production incident "
                    "investigation reasoning engine."
                ),
            },

            {
                "role": "user",
                "content": final_prompt,
            },
        ],

        format={

            "type": "object",

            "properties": {

                "summary": {
                    "type": "string",
                },

                "root_cause_hypothesis": {
                    "type": "string",
                },

                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },

                "recommended_actions": {

                    "type": "array",

                    "items": {
                        "type": "string",
                    },
                },
            },

            "required": [
                "summary",
                "root_cause_hypothesis",
                "confidence",
                "recommended_actions",
            ],
        },
    )

    # ========================================================
    # STEP 8 — PARSE FINAL RESPONSE
    # ========================================================

    content = (
        final_response[
            "message"
        ][
            "content"
        ]
    )

    try:

        data = json.loads(
            content
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "LLM returned invalid JSON for "
            f"final investigation: {error}"
        )

    # ========================================================
    # STEP 9 — VALIDATE
    # ========================================================

    summary = data.get(
        "summary"
    )

    root_cause_hypothesis = data.get(
        "root_cause_hypothesis"
    )

    confidence = data.get(
        "confidence"
    )

    recommended_actions = data.get(
        "recommended_actions"
    )

    if not isinstance(
        summary,
        str,
    ):

        raise ValueError(
            "Invalid summary returned by LLM."
        )

    if not isinstance(
        root_cause_hypothesis,
        str,
    ):

        raise ValueError(
            "Invalid root cause hypothesis returned by LLM."
        )

    if not isinstance(
        recommended_actions,
        list,
    ):

        raise ValueError(
            "Invalid recommended actions returned by LLM."
        )

    try:

        confidence = float(
            confidence
        )

    except (
        TypeError,
        ValueError,
    ):

        confidence = 0.0

    confidence = max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )

    # ========================================================
    # STEP 10 — CREATE STRUCTURED INVESTIGATION
    # ========================================================

    investigation = TicketInvestigation(

        summary=summary,

        evidence=verified_evidence,

        root_cause_hypothesis=(
            root_cause_hypothesis
        ),

        confidence=confidence,

        recommended_actions=[
            str(action)
            for action in recommended_actions
        ],

        sources=list(
            dict.fromkeys(
                item.source
                for item in verified_evidence
            )
        ),

        approval=ApprovalDecision(
            status="pending"
        ),
    )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print()
    print("=" * 70)
    print(
        "AI AGENT INVESTIGATION COMPLETE"
    )
    print("=" * 70)

    print(
        json.dumps(
            investigation.model_dump(),
            indent=2,
            default=str,
        )
    )

    return investigation


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    investigation = investigate_ticket(
        ticket_id=1
    )

    print()
    print("=" * 70)
    print(
        "FINAL STRUCTURED INVESTIGATION"
    )
    print("=" * 70)

    print(
        json.dumps(
            investigation.model_dump(),
            indent=2,
            default=str,
        )
    )