"""Append-only evidence writing for an individual evaluation run.

The store deliberately records observations and supervisor decisions separately.
It never selects a model, sends a candidate prompt, or makes an intervention.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import RunPhase, TerminalClass, transition_is_valid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass
class EvidenceStore:
    root: Path
    run_id: str
    phase: RunPhase = RunPhase.PREPARED
    _run_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        if not self.run_id or "/" in self.run_id or ".." in self.run_id:
            raise ValueError("run_id must be a simple non-empty identifier")
        self._run_dir = self.root / "runs" / self.run_id
        if self._run_dir.exists():
            raise FileExistsError(f"refusing to overwrite run evidence: {self._run_dir}")
        self._run_dir.mkdir(parents=True)
        (self._run_dir / "events.jsonl").touch()
        (self._run_dir / "interventions.jsonl").touch()
        _write_json(self._run_dir / "metrics.json", {"run_id": self.run_id, "created_at": utc_now()})

    @classmethod
    def resume(cls, root: Path, run_id: str) -> "EvidenceStore":
        """Re-open durable evidence without creating or overwriting files.

        A real candidate run is intentionally advanced one model turn at a
        time so its human supervisor can inspect it between turns.  This
        helper recovers the last recorded phase from the append-only event
        log.  It does not repair, truncate, or otherwise reinterpret history.
        """
        instance = object.__new__(cls)
        instance.root = root
        instance.run_id = run_id
        instance._run_dir = root / "runs" / run_id
        if not instance._run_dir.is_dir():
            raise FileNotFoundError(f"run evidence does not exist: {instance._run_dir}")
        instance.phase = RunPhase.PREPARED
        events = instance._run_dir / "events.jsonl"
        if events.exists():
            for line in events.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if record.get("type") == "phase_changed":
                    instance.phase = RunPhase(record["target"])
        return instance

    @property
    def run_dir(self) -> Path:
        return self._run_dir

    def write_once(self, name: str, value: dict[str, Any]) -> None:
        path = self._run_dir / name
        if path.exists():
            raise FileExistsError(f"evidence already exists: {path.name}")
        _write_json(path, value)

    def event(self, event_type: str, **payload: Any) -> None:
        record = {"at": utc_now(), "type": event_type, "phase": self.phase, **payload}
        with (self._run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def transition(self, target: RunPhase, reason: str) -> None:
        if not transition_is_valid(self.phase, target):
            raise ValueError(f"invalid run transition: {self.phase} -> {target}")
        previous = self.phase
        self.phase = target
        self.event("phase_changed", previous=previous, target=target, reason=reason)

    def intervention(self, intervention_class: str, decision: str, basis: str) -> None:
        if intervention_class == "I4_implementation_forbidden":
            raise ValueError("I4 must not be issued as benchmark assistance")
        record = {
            "at": utc_now(),
            "phase": self.phase,
            "class": intervention_class,
            "decision": decision,
            "basis": basis,
        }
        with (self._run_dir / "interventions.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def terminal(self, classification: TerminalClass, reason: str) -> None:
        self.transition(RunPhase.TERMINAL, reason)
        self.write_once("acceptance.json", {
            "terminal_class": classification,
            "reason": reason,
            "finished_at": utc_now(),
        })

    def summary(self, text: str) -> None:
        path = self._run_dir / "summary.md"
        if path.exists():
            raise FileExistsError("summary.md already exists")
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
