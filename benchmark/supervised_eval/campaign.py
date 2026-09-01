"""Durable, supervisor-driven state for the full local coding campaign.

This module is deliberately not an autonomous agent.  It owns only durable
campaign bookkeeping: Phase-0 evidence, the ordered candidate matrix, and a
small status projection.  Codex advances model turns through the existing
``PilotRunController`` after inspecting that projection.

All generated state belongs in the caller-supplied ignored evidence root.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CAMPAIGN_ID = "full-local-coding-campaign-20260901"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def campaign_state_path(root: Path) -> Path:
    return root / "campaign-state.json"


def preflight_path(root: Path) -> Path:
    return root / "phase0-preflight.json"


def write_once(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite campaign evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def initialize(root: Path, candidates: list[str]) -> dict[str, Any]:
    if len(candidates) != 9 or len(set(candidates)) != 9:
        raise ValueError("the full campaign requires exactly nine unique candidates")
    state = {
        "campaign_id": CAMPAIGN_ID,
        "created_at": utc_now(),
        "candidates": candidates,
        "tasks": ["code_review", "gallery"],
        "phase0_complete": False,
        "cells": {
            f"{candidate}-{task}": {"candidate": candidate, "task": task, "status": "pending"}
            for candidate in candidates
            for task in ("code_review", "gallery")
        },
    }
    write_once(campaign_state_path(root), state)
    return state


def load(root: Path) -> dict[str, Any]:
    return json.loads(campaign_state_path(root).read_text(encoding="utf-8"))


def save(root: Path, state: dict[str, Any]) -> None:
    campaign_state_path(root).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record_preflight(root: Path, payload: dict[str, Any]) -> None:
    if payload.get("campaign_id") != CAMPAIGN_ID:
        raise ValueError("preflight campaign_id does not match")
    if payload.get("status") != "passed":
        raise ValueError("only a passed Phase-0 preflight can close Phase 0")
    write_once(preflight_path(root), payload)
    state = load(root)
    state["phase0_complete"] = True
    state["phase0_completed_at"] = utc_now()
    save(root, state)


def set_cell(root: Path, cell_id: str, status: str, *, run_id: str | None = None, reason: str | None = None) -> None:
    state = load(root)
    cell = state["cells"].get(cell_id)
    if not isinstance(cell, dict):
        raise KeyError(f"unknown campaign cell: {cell_id}")
    if cell.get("status") == "terminal":
        raise RuntimeError(f"terminal campaign cell cannot be changed: {cell_id}")
    if status not in {"pending", "active", "terminal"}:
        raise ValueError("status must be pending, active, or terminal")
    cell["status"] = status
    cell["updated_at"] = utc_now()
    if run_id is not None:
        cell["run_id"] = run_id
    if reason is not None:
        cell["reason"] = reason
    save(root, state)


def compact_status(root: Path) -> dict[str, Any]:
    state = load(root)
    cells = list(state["cells"].values())
    return {
        "campaign_id": state["campaign_id"],
        "phase0_complete": state["phase0_complete"],
        "counts": {status: sum(cell.get("status") == status for cell in cells) for status in ("pending", "active", "terminal")},
        "active": [cell for cell in cells if cell.get("status") == "active"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Record/query full local coding campaign state")
    parser.add_argument("--evidence-root", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("initialize")
    init.add_argument("--candidate", action="append", required=True)
    preflight = commands.add_parser("record-preflight")
    preflight.add_argument("--input", required=True, type=Path)
    cell = commands.add_parser("cell")
    cell.add_argument("--id", required=True)
    cell.add_argument("--status", required=True)
    cell.add_argument("--run-id")
    cell.add_argument("--reason")
    commands.add_parser("status")
    args = parser.parse_args()
    if args.command == "initialize":
        print(json.dumps(initialize(args.evidence_root, args.candidate), sort_keys=True))
    elif args.command == "record-preflight":
        record_preflight(args.evidence_root, json.loads(args.input.read_text(encoding="utf-8")))
        print(json.dumps(compact_status(args.evidence_root), sort_keys=True))
    elif args.command == "cell":
        set_cell(args.evidence_root, args.id, args.status, run_id=args.run_id, reason=args.reason)
        print(json.dumps(compact_status(args.evidence_root), sort_keys=True))
    else:
        print(json.dumps(compact_status(args.evidence_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
