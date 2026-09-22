import json
import os

import ollama

from models.ticket import TicketAnalysis


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434"
)

ollama_client = ollama.Client(
    host=OLLAMA_HOST
)


# ============================================================
# TICKET ANALYSIS
# ============================================================

def analyze_ticket(
    customer: str,
    issue: str,
    context: str = ""
) -> TicketAnalysis:

    prompt = f"""
You are an AI customer support analyst.

Analyze the following customer support ticket.

CUSTOMER:
{customer}

ISSUE:
{issue}


INTERNAL COMPANY KNOWLEDGE:
{context}


IMPORTANT RULES:

1. Use the internal company knowledge when it is relevant.

2. Do not invent company-specific information.

3. The root cause must be presented as a hypothesis,
   not as a confirmed fact, unless the ticket or knowledge
   base clearly confirms it.

4. Recommended actions must be based on the internal
   company knowledge whenever possible.

5. If the internal knowledge does not contain enough
   information, say that more investigation is required.

6. Keep the response concise and practical.

7. Return only valid JSON.

8. Do not include explanations outside the JSON.


RETURN EXACTLY THESE FIELDS:

category

priority

summary

sentiment

root_cause

recommended_actions


PRIORITY MUST BE ONE OF:

low
medium
high
critical


SENTIMENT MUST BE ONE OF:

positive
neutral
negative
urgent


recommended_actions MUST BE AN ARRAY OF STRINGS.
"""

    response = ollama_client.chat(

        model="llama3.2",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        format={
            "type": "object",

            "properties": {

                "category": {
                    "type": "string"
                },

                "priority": {
                    "type": "string"
                },

                "summary": {
                    "type": "string"
                },

                "sentiment": {
                    "type": "string"
                },

                "root_cause": {
                    "type": "string"
                },

                "recommended_actions": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },

            "required": [

                "category",

                "priority",

                "summary",

                "sentiment",

                "root_cause",

                "recommended_actions"
            ]
        }
    )

    result = response[
        "message"
    ][
        "content"
    ]

    data = json.loads(
        result
    )

    validated_analysis = TicketAnalysis(
        **data
    )

    return validated_analysis