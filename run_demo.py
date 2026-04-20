import argparse
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single web safety scenario")
    parser.add_argument("--scenario", default=os.environ.get("WEB_SAFETY_SCENARIO", "pi-body-text-001"))
    parser.add_argument("--backend", choices=["mock", "openclaw", "openclaw_session"], default=os.environ.get("WEB_SAFETY_AGENT", "mock"))
    parser.add_argument("--agent", default=os.environ.get("WEB_SAFETY_OPENCLAW_AGENT", ""))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ["WEB_SAFETY_SCENARIO"] = args.scenario
    os.environ["WEB_SAFETY_AGENT"] = args.backend
    if args.agent:
        os.environ["WEB_SAFETY_OPENCLAW_AGENT"] = args.agent
    else:
        os.environ.pop("WEB_SAFETY_OPENCLAW_AGENT", None)

    from web_safety_eval.runner import run_named_scenario

    resolved_agent = args.agent or ("openclaw-default" if args.backend == "openclaw" else "unspecified")
    print(f"Running {args.scenario} with backend={args.backend} agent={resolved_agent}")
    result = run_named_scenario(args.scenario)
    print(f"Run complete: {result.run_dir}")
    print(f"Outcome: {result.outcome}")
    print(f"Report: {result.report_path}")


if __name__ == "__main__":
    main()
