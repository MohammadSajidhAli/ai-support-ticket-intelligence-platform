import json
import os
import time
from typing import Any, Dict

from google import genai


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is required."
    )


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


MAX_RETRIES = 3


def _generate_content(
    prompt: str,
    system_prompt: str | None = None,
    response_mime_type: str | None = None,
):
    config = {}

    if system_prompt:
        config["system_instruction"] = system_prompt

    if response_mime_type:
        config["response_mime_type"] = response_mime_type

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            response = client.models.generate_content(

                model=GEMINI_MODEL,

                contents=prompt,

                config=config
            )

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as exc:

            last_error = exc

            if attempt == MAX_RETRIES - 1:
                break

            wait_seconds = 2 ** attempt

            print(
                f"[GEMINI] Request failed "
                f"(attempt {attempt + 1}/{MAX_RETRIES}). "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        f"Gemini request failed after "
        f"{MAX_RETRIES} attempts: "
        f"{last_error}"
    )


def generate_response(
    prompt: str,
    system_prompt: str | None = None,
) -> str:

    return _generate_content(

        prompt=prompt,

        system_prompt=system_prompt
    )


def generate_json_response(
    prompt: str,
    system_prompt: str | None = None,
) -> Dict[str, Any]:

    response_text = _generate_content(

        prompt=prompt,

        system_prompt=system_prompt,

        response_mime_type="application/json"
    )

    try:

        return json.loads(
            response_text
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Gemini returned invalid JSON: "
            f"{response_text}"
        ) from exc


def analyze_ticket(
    ticket_data: dict
) -> Dict[str, Any]:

    prompt = f"""
Analyze the following customer support ticket.

TICKET:

{json.dumps(
    ticket_data,
    indent=2,
    default=str
)}

Return ONLY valid JSON with the following structure:

{{
    "category": "string",
    "priority": "string",
    "summary": "string",
    "sentiment": "string",
    "root_cause": "string",
    "recommended_actions": [
        "string"
    ]
}}

Rules:

1. Use only information present in the ticket.
2. Do not invent technical facts.
3. Keep the summary concise.
4. The root cause should be treated as a hypothesis.
5. Recommended actions should be relevant to the issue.
"""

    return generate_json_response(

        prompt=prompt,

        system_prompt=(
            "You are a support ticket analysis engine. "
            "Return only valid JSON and do not invent facts."
        )
    )