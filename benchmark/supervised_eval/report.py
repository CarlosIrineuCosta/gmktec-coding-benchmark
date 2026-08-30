"""Compact sanitized report rendering from durable run evidence."""
from __future__ import annotations

import json
from pathlib import Path


def render(run_dir: Path) -> str:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    acceptance = json.loads((run_dir / "acceptance.json").read_text(encoding="utf-8"))
    interventions = (run_dir / "interventions.jsonl").read_text(encoding="utf-8").splitlines()
    return "\n".join([
        f"# Evaluation run — {manifest['run_id']}",
        "",
        f"- Task family: {manifest['task_family']}",
        f"- Model: {manifest.get('model_label', 'not recorded')}",
        f"- Terminal class: {acceptance['terminal_class']}",
        f"- Terminal reason: {acceptance['reason']}",
        f"- Allowed interventions recorded: {len(interventions)}",
        "",
        "Raw trajectories and any sensitive material remain local under `data/private/`.",
        "",
    ])
