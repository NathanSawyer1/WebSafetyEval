from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from .install_skill import install_skill
from .runner import run_named_scenario

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = ROOT / "scenarios"
QUICKSTART_TEXT = """Quick start:
  web-safety-eval list-scenarios
  web-safety-eval list-agents
  web-safety-eval run --scenario pi-body-text-001
  web-safety-eval run --scenario pi-body-text-001 --backend openclaw
  web-safety-eval run --scenario pi-body-text-001 --backend openclaw --agent coder
  web-safety-eval run-all --backend openclaw --agent research-lite
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
AGENT_HELP_TEXT = f"""Use this tool when someone asks to test an OpenClaw agent against hostile web scenarios.

Suggested flow:
  1. Run web-safety-eval list-scenarios to see the real scenario IDs.
  2. Run web-safety-eval list-agents to see the real OpenClaw agent names before targeting one.
  3. If the user says "yourself" or wants the default OpenClaw agent, use --backend openclaw and omit --agent.
  4. If the user names an agent like coder or research-lite, add --backend openclaw --agent <name>.
  5. If the named agent is missing, ask the user to choose from the listed agents instead of guessing.
  6. Use run for one scenario or run-all when they want the whole suite.
  7. Share the run outcome, report path, and the most relevant failure signals.

Examples:
  web-safety-eval list-agents
  web-safety-eval run --backend openclaw --scenario pi-body-text-001
  web-safety-eval run --backend openclaw --agent coder --scenario pi-body-text-001
  web-safety-eval run-all --backend openclaw

{QUICKSTART_TEXT.rstrip()}

{RESULTS_TEXT.rstrip()}
"""


def _resolved_agent_label(backend: str, agent: str) -> str:
    return agent or ("openclaw-default" if backend == "openclaw" else "unspecified")


def _apply_agent_env(backend: str, agent: str) -> None:
    os.environ["WEB_SAFETY_AGENT"] = backend
    if agent:
        os.environ["WEB_SAFETY_OPENCLAW_AGENT"] = agent
    else:
        os.environ.pop("WEB_SAFETY_OPENCLAW_AGENT", None)


def _result_payload(result) -> dict[str, object]:
    return {
        "scenario_id": result.scenario_id,
        "outcome": result.outcome,
        "run_dir": str(result.run_dir) if result.run_dir else None,
        "report_path": str(result.report_path) if result.report_path else None,
        "failure_signals": [
            {
                "type": signal.type,
                "description": signal.description,
                "evidence_ref": signal.evidence_ref,
            }
            for signal in result.failure_signals
        ],
    }


def scenario_names() -> list[str]:
    return sorted(
        scenario_dir.name
        for scenario_dir in SCENARIOS_DIR.iterdir()
        if scenario_dir.is_dir() and (scenario_dir / "scenario.json").exists()
    )


def available_openclaw_agents() -> list[str]:
    completed = subprocess.run(
        ["openclaw", "agents", "list", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(completed.stdout)
    agents = [item["id"] for item in data]
    if not agents:
        raise RuntimeError("Could not parse any agent names from `openclaw agents list --json`")
    return agents


def _validate_named_agent(parser: argparse.ArgumentParser, backend: str, agent: str) -> None:
    if backend != "openclaw" or not agent:
        return
    try:
        agents = available_openclaw_agents()
    except (subprocess.CalledProcessError, FileNotFoundError, RuntimeError) as exc:
        parser.error(f"Unable to resolve available OpenClaw agents: {exc}")
    if agent not in agents:
        parser.error(f"Unknown OpenClaw agent: {agent}. Available agents: {', '.join(agents)}")


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
    run_parser.add_argument("--json", action="store_true", help="Print structured JSON output")

    run_all_parser = subparsers.add_parser(
        "run-all",
        help="Run all scenarios",
        epilog=QUICKSTART_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run_all_parser.add_argument("--backend", choices=["mock", "openclaw", "openclaw_session"], default=os.environ.get("WEB_SAFETY_AGENT", "mock"))
    run_all_parser.add_argument("--agent", default=os.environ.get("WEB_SAFETY_OPENCLAW_AGENT", ""))
    run_all_parser.add_argument("--json", action="store_true", help="Print structured JSON output")

    tui_parser = subparsers.add_parser("tui", help="Launch the terminal UI")
    tui_parser.add_argument("--backend", choices=["mock", "openclaw", "openclaw_session"], default=os.environ.get("WEB_SAFETY_AGENT", "mock"))
    tui_parser.add_argument("--agent", default=os.environ.get("WEB_SAFETY_OPENCLAW_AGENT", ""))

    install_skill_parser = subparsers.add_parser("install-skill", help="Install the packaged OpenClaw skill")
    install_skill_parser.add_argument("--target", help="Override the default OpenClaw skill directory")
    install_skill_parser.add_argument("--force", action="store_true", help="Overwrite an existing install")

    subparsers.add_parser("agent-help", help="Print a short primer for an OpenClaw agent using this tool")
    list_agents_parser = subparsers.add_parser("list-agents", help="List available OpenClaw agents")
    list_agents_parser.add_argument("--json", action="store_true", help="Print structured JSON output")
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

    if command == "agent-help":
        print(AGENT_HELP_TEXT.rstrip())
        return

    if command == "explain-results":
        print(RESULTS_TEXT.rstrip())
        return

    if command == "install-skill":
        destination = install_skill(target=args.target, force=args.force)
        print(f"Installed OpenClaw skill to {destination}")
        return

    if command == "list-agents":
        agents = available_openclaw_agents()
        if args.json:
            print(json.dumps({"agents": agents}))
            return
        for name in agents:
            print(name)
        return

    if command == "list-scenarios":
        for name in scenario_names():
            print(name)
        return

    if command == "run":
        _validate_named_agent(parser, args.backend, args.agent)
        _apply_agent_env(args.backend, args.agent)
        os.environ["WEB_SAFETY_SCENARIO"] = args.scenario
        resolved_agent = _resolved_agent_label(args.backend, args.agent)
        result = run_named_scenario(args.scenario)
        if args.json:
            print(json.dumps(_result_payload(result)))
            return
        print(f"Running {args.scenario} with backend={args.backend} agent={resolved_agent}")
        print(f"Run complete: {result.run_dir}")
        print(f"Outcome: {result.outcome}")
        print(f"Report: {result.report_path}")
        print("For result semantics, run: web-safety-eval explain-results")
        return

    if command == "run-all":
        _validate_named_agent(parser, args.backend, args.agent)
        _apply_agent_env(args.backend, args.agent)
        resolved_agent = _resolved_agent_label(args.backend, args.agent)
        results = [run_named_scenario(name) for name in scenario_names()]
        if args.json:
            summary = {
                "failed": sum(1 for result in results if result.outcome == "failed"),
                "did_not_fail": sum(1 for result in results if result.outcome == "did_not_fail"),
                "total": len(results),
            }
            print(json.dumps({"results": [_result_payload(result) for result in results], "summary": summary}))
            return
        print(f"Running all scenarios with backend={args.backend} agent={resolved_agent}")
        for result in results:
            print(f"{result.scenario_id}: {result.outcome} ({result.report_path})")

        failed = sum(1 for result in results if result.outcome == "failed")
        did_not_fail = sum(1 for result in results if result.outcome == "did_not_fail")
        print()
        print(f"Summary: {failed} failed, {did_not_fail} did_not_fail, {len(results)} total")
        print("For result semantics, run: web-safety-eval explain-results")
        return

    parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
