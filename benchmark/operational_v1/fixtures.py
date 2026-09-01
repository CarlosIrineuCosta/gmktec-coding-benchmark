"""Synthetic public operational-v1 task fixtures only."""
from __future__ import annotations

from copy import deepcopy

LABELS = ("task_action", "decision", "blocker", "factual_reference", "request", "note", "discard", "ambiguous")
CLASSIFICATION_ITEMS = [
    {"id": "cls-01", "text": "Enviar o resumo ao cliente antes das 15h", "label": "task_action", "review": False},
    {"id": "cls-02", "text": "Decisão: manter o endpoint interno até a revisão", "label": "decision", "review": False},
    {"id": "cls-03", "text": "Blocked: pytest is missing from the runner venv", "label": "blocker", "review": False},
    {"id": "cls-04", "text": "model-manifest-q4km.json", "label": "factual_reference", "review": False},
    {"id": "cls-05", "text": "Você pode confirmar qual porta está liberada?", "label": "request", "review": False},
    {"id": "cls-06", "text": "Nota pessoal: comparar isso depois do almoço", "label": "note", "review": False},
    {"id": "cls-07", "text": "okkkkk...", "label": "discard", "review": False},
    {"id": "cls-08", "text": "maybe route this?", "label": "ambiguous", "review": True},
    {"id": "cls-09", "text": "FLOOR-188: no deploy; validate only", "label": "factual_reference", "review": False},
    {"id": "cls-10", "text": "Erro?? servidor caiu ou só a VPN?", "label": "ambiguous", "review": True},
]
EXTRACTION_SOURCES = {
    "ext-a": """Setup record 2026-08-16\nModel: translategemma:12b\nDigest: c2f9a9ca1ec7149f2422581c89937ab0363d9399d9355514d753ee012e99c252\nCommand: python3 -m benchmark.operational_v1.run --task classification\nDecision: use temperature 0.\nOpen question: effective context is not reported by this backend.""",
    "ext-b": """Meeting fragment\nEarlier note: port 8081 is the production endpoint.\nSuperseded 2026-08-16: port 8081 is an experiment-only loopback endpoint.\nBlocker: no model may run concurrently with another resident model.\nPath: data/private/results/operational_v1/.""",
}
DOCS = {
    "doc-a": "# Run rule\nThe direct client uses http://gmktec:11434/v1. Record backend identity in every result. Do not claim endpoint identity proves model quality.",
    "doc-b": "# Revision note\nOld statement (superseded): repeat every failed run three times.\nCurrent statement: diagnose a serving failure once, record it, then continue with the remaining roster.\nA quality result needs no tool access.",
    "doc-c": "# Safety rule\nA model may be called safe unattended only after three materially consistent valid runs for that task. A useful report with an unsupported claim is review-only.",
}
REPORT_RECORDS = [
    {"model": "alpha", "task": "classification", "status": "completed", "accuracy": 0.9, "latency_s": 12.4},
    {"model": "alpha", "task": "extraction", "status": "serving_failure", "accuracy": None, "latency_s": 0.0},
    {"model": "beta", "task": "classification", "status": "completed", "accuracy": 0.5, "latency_s": 9.1},
]
CODE_FILES = {
    "priority.py": "def normalize(priority: str) -> str:\n    return priority.strip().lower()\n\n\ndef is_urgent(priority: str) -> bool:\n    return normalize(priority) == \"urgent\"\n",
    "queue.py": "from priority import is_urgent\n\n\ndef route(priority: str) -> str:\n    return \"fast\" if priority == \"urgent\" else \"normal\"\n",
    "test_queue.py": "from queue import route\n\n\ndef test_urgent_with_spaces_uses_fast_route():\n    assert route(\" Urgent \") == \"fast\"\n\n\ndef test_unknown_priority_is_normal():\n    assert route(\"later\") == \"normal\"\n",
}


def fixture(task_id: str) -> dict:
    if task_id == "classification": return {"task": task_id, "labels": LABELS, "items": deepcopy(CLASSIFICATION_ITEMS)}
    if task_id == "extraction": return {"task": task_id, "sources": deepcopy(EXTRACTION_SOURCES)}
    if task_id == "docs_qa": return {"task": task_id, "documents": deepcopy(DOCS), "questions": ["Which endpoint is used by the direct client?", "What is the current policy for a serving failure?", "When is safe unattended allowed?", "What is the model digest?"]}
    if task_id == "report": return {"task": task_id, "records": deepcopy(REPORT_RECORDS)}
    if task_id == "patch": return {"task": task_id, "files": deepcopy(CODE_FILES), "request": "Make route treat the exact normalized value 'urgent' as fast. Return only a unified diff."}
    raise ValueError(f"unknown task: {task_id}")
