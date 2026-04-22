from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import RunResult


MAX_EVIDENCE_CHARS = 240
MAX_ATTACKER_TRIED_CHARS = 200


def _why_it_matters(result: RunResult) -> str:
    if result.outcome == "failed":
        category = (result.category or "this category").replace("_", " ")
        severity = (result.severity_if_failed or "unknown").lower()
        return f"This scenario exposed a {category} failure path. If this behavior appeared in production, the impact could be {severity}."
    if result.success_description:
        return f"This run did not exhibit the targeted failure mode. Intended safe behavior: {result.success_description}"
    return "This run did not exhibit the targeted failure mode in this controlled scenario."


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def _format_evidence_block(content: str | None) -> list[str]:
    if not content:
        return ["  - Matched content: `(not captured)`"]
    clipped = _clip(content, MAX_EVIDENCE_CHARS)
    return [
        "  - Matched content:",
        "",
        "    ```text",
        f"    {clipped}",
        "    ```",
    ]


def _strip_html(text: str) -> str:
    for token in ["<br>", "<br/>", "<br />", "</p>", "</div>", "</li>", "</h1>", "</h2>", "</h3>"]:
        text = text.replace(token, "\n")
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _load_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _attacker_tried_lines(result: RunResult) -> list[str]:
    assert result.run_dir is not None
    tool_calls = _load_json_if_exists(result.run_dir / "tool_calls.json") or []
    pages_dir = result.run_dir / "pages"
    snippets: list[str] = []
    seen: set[str] = set()

    for call in tool_calls:
        page = ((call or {}).get("result") or {}).get("page")
        if not page or page in seen:
            continue
        page_path = pages_dir / page
        if not page_path.exists():
            continue
        seen.add(page)
        raw = page_path.read_text(encoding="utf-8")
        snippet = _clip(_strip_html(raw), MAX_ATTACKER_TRIED_CHARS)
        if snippet:
            snippets.append(f"- `{page}`: {snippet}")

    return snippets or ["- No hostile page content was captured for this run."]


def write_markdown_report(result: RunResult) -> Path:
    assert result.run_dir is not None
    report_path = result.run_dir / "report.md"
    lines = [
        f"# Report: {result.scenario_id}",
        "",
        f"Outcome: **{result.outcome}**",
        f"Category: **{(result.category or 'unknown').replace('_', ' ')}**",
        f"Agent under test: **{((result.agent or {}).get('agent') or 'unknown')}** (backend: {((result.agent or {}).get('backend') or 'unknown')})",
        f"Scenario severity if failed: **{result.severity_if_failed or 'unknown'}**",
        "",
        "## Why it matters",
        "",
        _why_it_matters(result),
        "",
        "## What the attacker tried",
        "",
        *_attacker_tried_lines(result),
        "",
        "## Findings",
    ]
    if result.failure_signals:
        for signal in result.failure_signals:
            lines.append(f"- **{signal.type}**: {signal.description}")
            lines.extend(_format_evidence_block(signal.matched_content))
            lines.append(f"  - Evidence pointer: `{signal.evidence_ref or 'n/a'}`")
    else:
        lines.append("- No failure signals detected")

    evidence_summary = [signal.evidence_ref for signal in result.failure_signals if signal.evidence_ref]
    lines.extend([
        "",
        "## Evidence summary",
        "",
    ])
    if evidence_summary:
        for ref in evidence_summary:
            lines.append(f"- `{ref}`")
    else:
        lines.append("- No direct evidence references were recorded for this run.")

    lines.extend([
        "",
        "## Final answer",
        "",
        result.final_answer or "(none)",
        "",
        "## Caveat",
        "",
        "This evaluation covers a specific controlled scenario. It is not a safety certification.",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
