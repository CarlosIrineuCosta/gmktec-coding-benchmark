"""Finding-level scoring for a private code-review ledger.

The candidate review and gold fixture remain private.  This module consumes a
private ledger that assigns at most one gold defect to each reported finding.
It emits only aggregate counts suitable for a sanitized report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def score_finding_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    findings = ledger.get("reported_finding_ids")
    gold = ledger.get("gold_defect_ids")
    matches = ledger.get("matches")
    if not isinstance(findings, list) or not all(isinstance(item, str) and item for item in findings):
        raise ValueError("reported_finding_ids must be a list of non-empty strings")
    if len(set(findings)) != len(findings):
        raise ValueError("reported_finding_ids must be unique")
    if not isinstance(gold, list) or not gold or not all(isinstance(item, str) and item for item in gold):
        raise ValueError("gold_defect_ids must be a non-empty list of strings")
    if len(set(gold)) != len(gold):
        raise ValueError("gold_defect_ids must be unique")
    if not isinstance(matches, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in matches.items()):
        raise ValueError("matches must map finding ids to gold ids")
    if not set(matches).issubset(findings):
        raise ValueError("matches contains an unknown finding id")
    if not set(matches.values()).issubset(gold):
        raise ValueError("matches contains an unknown gold id")
    if len(set(matches.values())) != len(matches):
        raise ValueError("a gold defect can credit at most one reported finding")

    credited = len(matches)
    total = len(findings)
    return {
        "scoring_unit": "finding",
        "reported_findings": total,
        "credited_findings": credited,
        "false_or_non_gold_findings": total - credited,
        "gold_defects": len(gold),
        "matched_gold_defects": credited,
        "recall": credited / len(gold),
        "precision": credited / total if total else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a private finding-level review ledger")
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.ledger.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ledger must be a JSON object")
    result = score_finding_ledger(payload)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
