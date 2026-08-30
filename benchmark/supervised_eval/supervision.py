"""Supervisor decision helpers; they report observations, never auto-intervene."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable


@dataclass(frozen=True)
class SupervisionDecision:
    checkpoint: int
    progress_observed: bool
    recommendation: str
    basis: str


class LoopDetector:
    """Detect unchanged repeated actions without deciding what to tell a model."""

    def __init__(self) -> None:
        self._last: str | None = None
        self._repeats = 0

    def observe(self, action: str, state_fingerprint: str) -> int:
        fingerprint = sha256(f"{action}\0{state_fingerprint}".encode()).hexdigest()
        if fingerprint == self._last:
            self._repeats += 1
        else:
            self._last = fingerprint
            self._repeats = 0
        return self._repeats

    def decision(self, checkpoint: int, meaningful_progress: bool, recent_actions: Iterable[str]) -> SupervisionDecision:
        actions = list(recent_actions)
        if meaningful_progress:
            return SupervisionDecision(checkpoint, True, "continue", "meaningful progress observed")
        if self._repeats >= 1:
            return SupervisionDecision(checkpoint, False, "inspect_for_intervention", "unchanged action/state repeated")
        if not actions:
            return SupervisionDecision(checkpoint, False, "inspect_for_intervention", "no observable action")
        return SupervisionDecision(checkpoint, False, "continue_with_close_watch", "no progress but no loop fingerprint")
