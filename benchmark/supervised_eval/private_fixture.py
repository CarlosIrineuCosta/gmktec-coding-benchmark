"""Local-only validation for private held-out code-review data."""
from __future__ import annotations

import json
from pathlib import Path


def validate_private_code_review_fixture(root: Path) -> dict[str, int]:
    fixture = root / "fixture" / "service.py"
    gold = root / "gold.json"
    if not fixture.is_file() or not gold.is_file():
        raise FileNotFoundError("private code-review fixture or gold data is missing")
    payload = json.loads(gold.read_text(encoding="utf-8"))
    defects = payload.get("defects")
    if not isinstance(defects, list) or not defects:
        raise ValueError("private gold must contain at least one defect")
    if payload.get("maximum_findings") != 8:
        raise ValueError("private review contract must retain eight-finding ceiling")
    return {"gold_defects": len(defects), "fixture_bytes": fixture.stat().st_size}
