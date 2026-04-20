from __future__ import annotations

from dataclasses import dataclass

from textual.message import Message

from .events import RunEvent


@dataclass
class RunEventMessage(Message):
    event: RunEvent
