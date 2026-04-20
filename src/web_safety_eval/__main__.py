from __future__ import annotations

import argparse
import os
from pathlib import Path

from .runner import run_named_scenario

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = ROOT / "scenarios"
QUICKSTART_TEXT = """Quick start:
  web-safety-eval list-scenarios
  web-safety-eval run --scenario pi-body-text-001
  web-safety-eval run --scenario pi-body-text-001 --backend openclaw
  web-safety-eval run --scenario pi-body-text-001 --backend openclaw --agent codex
  web-safety-eval run-all --backend openclaw --agent claude
  web-safety-eval explain-results

Notes:
  - Omit --agent to use the default OpenClaw agent.
  - If the console script is unavailable, use: python -m web_safety_eval ...
"""
RESULTS_TEXT = """How to read results:
  - failed: the harness detected one or more configured failure signals for the scenario.
  - did_not_fail: the harness did not detect those failure signals in this run.

Look here next:
  - report.md: human-readable summary and evidence
  - result.json: structured outcome, metadata, and failure signals
  - transcript.json: full turn-by-turn interaction record
  - tool_calls.json: recorded tool calls and tool results

Important:
  - did_not_fail does not prove the agent is universally safe.
  - It only means this run did not trigger the scenario's current checks.
"""


def _resolved_agent_label(backend: str, agent: str) -> str:
    return agent or ("openclaw-default" if backend == "openclaw" else "unspecified")


def _apply_agent_env(backend: str, agent: str) -> None:
    os.environ["WEB_SAFETY_AGENT"] = backend
    if agent:
        os.environ["WEB_SAFETY_OPENCLAW_AGENT"] = agent
    else:
        os.environ.pop("WEB_SAFETY_OPENCLAW_AGENT", None)


def scenario_names() -> list[str]:
    return sorted(
        scenario_dir.name
        for scenario_dir in SCENARIOS_DIR.iterdir()
        if scenario_dir.is_dir() and (scenario_dir / "scenario.json").exists()
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run web safety evaluation scenarios",
        epilog=QUICKSTART_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run a single scenario",
        epilog=QUICKSTART_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run_parser.add_argument("--scenario", default=os.environ.get("WEB_SAFETY_SCENARIO", "pi-body-text-001"))
    run_parser.add_argument("--backend", choices=["mock", "openclaw", "openclaw_session"], default=os.environ.get("WEB_SAFETY_AGENT", "mock"))
    run_parser.add_argument("--agent", default=os.environ.get("WEB_SAFETY_OPENCLAW_AGENT", ""))

    run_all_parser = subparsers.add_parser(
        "run-all",
        help="Run all scenarios",
        epilog=QUICKSTART_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run_all_parser.add_argument("--backend", choices=["mock", "openclaw", "openclaw_session"], default=os.environ.get("WEB_SAFETY_AGENT", "mock"))
    run_all_parser.add_argument("--agent", default=os.environ.get("WEB_SAFETY_OPENCLAW_AGENT", ""))

    tui_parser = subparsers.add_parser("tui", help="Launch the terminal UI")
    tui_parser.add_argument("--backend", choices=["mock", "openclaw", "openclaw_session"], default=os.environ.get("WEB_SAFETY_AGENT", "mock"))
    tui_parser.add_argument("--agent", default=os.environ.get("WEB_SAFETY_OPENCLAW_AGENT", ""))

    subparsers.add_parser("list-scenarios", help="List available scenarios")
    subparsers.add_parser("quickstart", help="Print copy-paste usage examples")
    subparsers.add_parser("explain-results", help="Explain outcome labels and where to inspect artifacts")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    command = args.command

    if command is None:
        parser.print_help()
        print()
        print("Try: web-safety-eval quickstart")
        return

    if command == "tui":
        try:
            from .tui import launch
        except ImportError as e:
            print(f"Textual is required for `tui`. Install with: pip install 'web-safety-eval[tui]'\n({e})")
            raise SystemExit(2)
        launch(backend=args.backend, agent=args.agent)
        return

    if command == "quickstart":
        print(QUICKSTART_TEXT.rstrip())
        return

    if command == "explain-results":
        print(RESULTS_TEXT.rstrip())
        return

    if command == "list-scenarios":
        for name in scenario_names():
            print(name)
        return

    if command == "run":
        _apply_agent_env(args.backend, args.agent)
        os.environ["WEB_SAFETY_SCENARIO"] = args.scenario
        resolved_agent = _resolved_agent_label(args.backend, args.agent)
        print(f"Running {args.scenario} with backend={args.backend} agent={resolved_agent}")
        result = run_named_scenario(args.scenario)
        print(f"Run complete: {result.run_dir}")
        print(f"Outcome: {result.outcome}")
        print(f"Report: {result.report_path}")
        print("For result semantics, run: web-safety-eval explain-results")
        return

    if command == "run-all":
        _apply_agent_env(args.backend, args.agent)
        resolved_agent = _resolved_agent_label(args.backend, args.agent)
        print(f"Running all scenarios with backend={args.backend} agent={resolved_agent}")
        results = []
        for name in scenario_names():
            result = run_named_scenario(name)
            results.append(result)
            print(f"{name}: {result.outcome} ({result.report_path})")

        failed = sum(1 for result in results if result.outcome == "failed")
        did_not_fail = sum(1 for result in results if result.outcome == "did_not_fail")
        print()
        print(f"Summary: {failed} failed, {did_not_fail} did_not_fail, {len(results)} total")
        print("For result semantics, run: web-safety-eval explain-results")
        return

    parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
