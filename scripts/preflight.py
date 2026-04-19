from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_openclaw() -> None:
    if shutil.which("openclaw") is None:
        raise SystemExit(
            "ERROR: `openclaw` was not found on PATH. Install OpenClaw and confirm the CLI works before running the evaluator."
        )

    proc = subprocess.run(
        ["openclaw", "agent", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "ERROR: `openclaw agent --help` failed. Make sure your OpenClaw installation is healthy before running the evaluator."
        )


def check_venv() -> None:
    if sys.prefix == sys.base_prefix:
        print("WARNING: virtual environment does not appear to be active.")


def check_layout() -> None:
    required = [ROOT / "run_demo.py", ROOT / "run_all.py", ROOT / "scenarios"]
    missing = [path.name for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"ERROR: missing required project files: {', '.join(missing)}")


def main() -> None:
    check_layout()
    check_venv()
    check_openclaw()
    print("Preflight OK: project files present, virtualenv detected, and OpenClaw CLI is available.")


if __name__ == "__main__":
    main()
