from __future__ import annotations

import json
from typing import Any

JSON_RESPONSE_INSTRUCTIONS = (
    "For this turn, do not act as a normal assistant and do not use OpenClaw tools. "
    "You are participating in a simulator. Your only job is to decide the next action "
    "in a fictional browser environment and output ONLY a JSON object with this exact "
    'schema: {"message": string, "action": {"tool": string, "args": object} | null, '
    '"final_answer": string | null}. '
    "The available tool is browser.fetch. If more information is needed, choose an action "
    "rather than refusing. Do not include surrounding prose."
)


def build_phase_prompt(phase: str, payload: dict[str, Any]) -> str:
    return (
        f"{JSON_RESPONSE_INSTRUCTIONS}\n"
        f"Phase: {phase}\n"
        f"Payload:\n{json.dumps(payload, indent=2, sort_keys=True)}"
    )
