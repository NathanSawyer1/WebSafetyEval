from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Iterator

from .events import RunEvent, parse_line


def tail_events(run_dir: Path, *, stop: threading.Event, poll_s: float = 0.15) -> Iterator[RunEvent]:
    path = run_dir / "events.jsonl"
    run_id = run_dir.name
    pos = 0
    buf = ""
    while not stop.is_set():
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                fh.seek(pos)
                chunk = fh.read()
                pos = fh.tell()
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                evt = parse_line(run_id, line)
                if evt is not None:
                    yield evt
                    if evt.kind in {"run_completed", "run_cancelled"}:
                        return
        time.sleep(poll_s)
