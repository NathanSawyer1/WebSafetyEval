from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))
ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT / "scenarios"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all web safety scenarios")
    parser.add_argument("--backend", choices=["mock", "openclaw", "openclaw_session"], default=os.environ.get("WEB_SAFETY_AGENT", "mock"))
    parser.add_argument("--agent", default=os.environ.get("WEB_SAFETY_OPENCLAW_AGENT", ""))
    return parser.parse_args()


def scenario_names() -> list[str]:
    return sorted(
        scenario_dir.name
        for scenario_dir in SCENARIOS_DIR.iterdir()
        if scenario_dir.is_dir() and (scenario_dir / "scenario.json").exists()
    )


def main() -> None:
    args = parse_args()
    os.environ["WEB_SAFETY_AGENT"] = args.backend
    if args.agent:
        os.environ["WEB_SAFETY_OPENCLAW_AGENT"] = args.agent
    else:
        os.environ.pop("WEB_SAFETY_OPENCLAW_AGENT", None)

    from web_safety_eval.runner import run_named_scenario

    resolved_agent = args.agent or ("openclaw-default" if args.backend == "openclaw" else "unspecified")
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


if __name__ == "__main__":
    main()
