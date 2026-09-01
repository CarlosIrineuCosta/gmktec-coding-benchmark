"""Strict direct-inference prompts, with no agent or tool surface."""
from __future__ import annotations

import json
from .fixtures import fixture


def prompt(task_id: str) -> str:
    data = fixture(task_id); body = json.dumps(data, ensure_ascii=False, indent=2)
    common = "Use only the supplied synthetic material. Do not use tools, web access, or unstated facts."
    if task_id == "classification": return f"{common}\nReturn JSON {{\"items\":[...]}}. Each item: id, primary_label (one supplied label), secondary_label (string or null), confidence (0..1), needs_review (boolean), reason (max 16 words).\nINPUT:\n{body}"
    if task_id == "extraction": return f"{common}\nReturn JSON {{\"documents\":[...]}}. For each source preserve entities, versions, paths, commands, dates, decisions, unresolved_questions, blockers, and source_id. Use null or [] for absent fields; distinguish superseded from current claims.\nINPUT:\n{body}"
    if task_id == "docs_qa": return f"{common}\nReturn JSON {{\"answers\":[{{\"question\":...,\"answer\":...,\"sources\":[{{\"id\":...,\"passage\":...}}]}}]}}. Answer 'not established by supplied documents' when appropriate.\nINPUT:\n{body}"
    if task_id == "report": return f"{common}\nReturn compact Markdown with exactly these headings: Completed, Failed, Unknown, Safety concerns, Routing, Next action. Preserve every number and do not call a serving failure a quality failure.\nINPUT:\n{body}"
    if task_id == "patch": return f"{common}\nReturn only a unified diff. {data['request']}\nFILES:\n{json.dumps(data['files'], ensure_ascii=False, indent=2)}"
    raise ValueError(task_id)
