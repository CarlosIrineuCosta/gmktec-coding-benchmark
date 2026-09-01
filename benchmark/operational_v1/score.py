"""Deterministic checks for operational-v1; never calls a model."""
from __future__ import annotations

import json
import re
from pathlib import Path
from .fixtures import CLASSIFICATION_ITEMS, LABELS, EXTRACTION_SOURCES


def _json(text: str):
    try: return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        return json.loads(text[start:end + 1]) if start >= 0 and end > start else None


def score(task_id: str, answer: str, output: Path | None = None) -> dict:
    result = {"task": task_id, "schema_valid": False, "correctness": None, "details": {}}
    parsed = _json(answer) if task_id not in {"report", "patch"} else None
    if task_id == "classification":
        rows = parsed.get("items", []) if isinstance(parsed, dict) else []; gold = {x["id"]: x for x in CLASSIFICATION_ITEMS}
        valid = len(rows) == len(gold) and all(isinstance(x, dict) and x.get("id") in gold and x.get("primary_label") in LABELS and isinstance(x.get("needs_review"), bool) and isinstance(x.get("confidence"), (int, float)) and isinstance(x.get("reason"), str) for x in rows)
        correct = sum(x.get("primary_label") == gold[x.get("id")]["label"] and x.get("needs_review") == gold[x.get("id")]["review"] for x in rows if x.get("id") in gold)
        result.update(schema_valid=valid, correctness=correct / len(gold), details={"correct": correct, "total": len(gold)})
    elif task_id == "extraction":
        rows = parsed.get("documents", []) if isinstance(parsed, dict) else []; rendered = json.dumps(rows, ensure_ascii=False)
        required = ["translategemma:12b", "python3 -m benchmark.operational_v1.run --task classification", "2026-08-16", "experiment-only"]
        result.update(schema_valid=isinstance(rows, list) and len(rows) == len(EXTRACTION_SOURCES), correctness=sum(x in rendered for x in required) / len(required), details={"required_literals": required})
    elif task_id == "docs_qa":
        rows = parsed.get("answers", []) if isinstance(parsed, dict) else []; joined = json.dumps(rows, ensure_ascii=False).lower(); expected = ["gmktec:11434/v1", "diagnose", "three", "not established"]
        result.update(schema_valid=isinstance(rows, list) and len(rows) == 4, correctness=sum(x in joined for x in expected) / len(expected), details={"expected": expected})
    elif task_id == "report":
        headings = ["completed", "failed", "unknown", "safety concerns", "routing", "next action"]
        result.update(schema_valid=all(re.search(rf"^#+\s+{re.escape(x)}\s*$", answer, re.I | re.M) for x in headings), correctness=float("alpha" in answer and "0.9" in answer and "serving" in answer.lower()), details={"headings": headings})
    elif task_id == "patch":
        normalized = answer.strip()
        if normalized.startswith("```diff") and normalized.endswith("```"):
            normalized = "\n".join(normalized.splitlines()[1:-1]).strip()
        result.update(schema_valid=(normalized.startswith("--- ") or normalized.startswith("diff --git")) and "+++ " in normalized and "route" in normalized, details={"requires_apply_and_test": True})
    else: raise ValueError(task_id)
    if output: output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
