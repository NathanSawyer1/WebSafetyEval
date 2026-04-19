from __future__ import annotations

import json


def extract_json_span(raw: str) -> str:
    text = raw.strip()
    if not text:
        raise ValueError("Empty response received; expected a JSON object.")

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    in_string = False
    escape = False
    depth = 0
    end = None
    start = None

    for idx in range(len(text) - 1, -1, -1):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == '}':
            if end is None:
                end = idx
            depth += 1
        elif ch == '{' and depth:
            depth -= 1
            if depth == 0:
                start = idx
                candidate = text[start:end + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    start = None
                    end = None

    raise ValueError(f"Could not parse JSON from response: {raw}")
