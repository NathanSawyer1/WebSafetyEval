from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

from web_safety_eval.__main__ import main


if __name__ == "__main__":
    sys.argv[0] = "run_demo.py"
    sys.argv[1:1] = ["run"]
    main()
