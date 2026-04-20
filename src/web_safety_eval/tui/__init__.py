from __future__ import annotations


def launch(*, backend: str = "mock", agent: str = "") -> None:
    from .app import launch as _launch
    _launch(backend=backend, agent=agent)
