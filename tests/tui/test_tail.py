from __future__ import annotations

import threading
import time

from web_safety_eval.tui.tail import tail_events


def test_tail_events_yields_incremental_lines(tmp_path):
    run_dir = tmp_path / 'run-1'
    run_dir.mkdir()
    events_path = run_dir / 'events.jsonl'
    stop = threading.Event()
    yielded = []

    def writer():
        with events_path.open('w', encoding='utf-8') as fh:
            fh.write('{"ts":1.0,"kind":"run_started","scenario_id":"pi"}\n')
            fh.flush()
            time.sleep(0.05)
            fh.write('{"ts":2.0,"kind":"run_completed","outcome":"did_not_fail","failure_count":0}\n')
            fh.flush()

    thread = threading.Thread(target=writer)
    thread.start()
    for evt in tail_events(run_dir, stop=stop, poll_s=0.01):
        yielded.append(evt.kind)
    thread.join()
    assert yielded == ['run_started', 'run_completed']
