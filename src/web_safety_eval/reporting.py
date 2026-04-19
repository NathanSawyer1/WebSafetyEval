from __future__ import annotations

from pathlib import Path

from .models import RunResult


def _why_it_matters(result: RunResult) -> str:
    if result.outcome == "failed":
        category = (result.category or "this category").replace("_", " ")
        severity = (result.severity_if_failed or "unknown").lower()
        return f"This scenario exposed a {category} failure path. If this behavior appeared in production, the impact could be {severity}."
    if result.success_description:
        return f"This run did not exhibit the targeted failure mode. Intended safe behavior: {result.success_description}"
    return "This run did not exhibit the targeted failure mode in this controlled scenario."


def write_markdown_report(result: RunResult) -> Path:
    assert result.run_dir is not None
    report_path = result.run_dir / "report.md"
    lines = [
        f"# Report: {result.scenario_id}",
        "",
        f"Outcome: **{result.outcome}**",
        f"Category: **{(result.category or 'unknown').replace('_', ' ')}**",
        f"Scenario severity if failed: **{result.severity_if_failed or 'unknown'}**",
        "",
        "## Why it matters",
        "",
        _why_it_matters(result),
        "",
        "## Findings",
    ]
    if result.failure_signals:
        for signal in result.failure_signals:
            lines.extend([
                f"- **{signal.type}**: {signal.description}",
                f"  - Evidence: `{signal.evidence_ref or 'n/a'}`",
            ])
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
