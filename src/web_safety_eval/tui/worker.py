from __future__ import annotations

import os
import threading

from ..runner import run_named_scenario


def run_scenario_worker(scenario_id: str, backend: str, agent: str, cancel_token: threading.Event):
    os.environ['WEB_SAFETY_AGENT'] = backend
    if agent:
        os.environ['WEB_SAFETY_OPENCLAW_AGENT'] = agent
    else:
        os.environ.pop('WEB_SAFETY_OPENCLAW_AGENT', None)
    return run_named_scenario(scenario_id, cancel_token=cancel_token)
