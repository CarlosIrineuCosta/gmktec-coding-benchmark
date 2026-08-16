"""Strict local coding canaries for one llama-server model.

This is intentionally much smaller than a coding CLI: it offers a single
repository_action function and rejects malformed, duplicate, or out-of-scope
actions.  It is designed to run as the restricted ``llm-runner`` Unix account.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASKS: dict[str, dict[str, str]] = {
    "normalize_tag": {
        "module": '''def normalize_tag(value: str) -> str:\n    \"\"\"Return a normalized tag without surrounding whitespace.\"\"\"\n    return value.lower()\n''',
        "test": '''from module import normalize_tag\n\n\ndef test_normalize_tag():\n    assert normalize_tag("  Urgent  ") == "urgent"\n\n\ntest_normalize_tag()\n''',
        "outcome": "normalize_tag must strip surrounding whitespace and lowercase its input.",
    },
    "parse_priority": {
        "module": '''def parse_priority(value: str) -> str:\n    \"\"\"Return a portable priority key.\"\"\"\n    return value.strip().lower().replace(" ", "_")\n''',
        "test": '''from module import parse_priority\n\n\ndef test_parse_priority():\n    assert parse_priority(" High Priority ") == "high-priority"\n\n\ntest_parse_priority()\n''',
        "outcome": "parse_priority must strip surrounding whitespace, lowercase its input, and join its words with one hyphen.",
    },
    "render_label": {
        "module": '''def render_label(prefix: str, value: str) -> str:\n    \"\"\"Render a short label.\"\"\"\n    return f"{prefix}: {value}"\n''',
        "test": '''from module import render_label\n\n\ndef test_render_label():\n    assert render_label("TODO", "  Buy milk  ") == "TODO: Buy milk"\n\n\ntest_render_label()\n''',
        "outcome": "render_label must preserve prefix and value content but strip only surrounding whitespace from value before rendering '<prefix>: <value>'.",
    },
}

TOOL = {
    "type": "function",
    "function": {
        "name": "repository_action",
        "description": "Perform exactly one allowed operation in the isolated task directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["read_file", "write_file", "run_test"]},
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["action"],
        },
    },
}


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json(url: str) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None


def get_text(url: str) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return response.read().decode(errors="replace")
    except Exception:
        return None


def chat(base_url: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    payload: dict[str, Any] = {
        "model": "qwen3-coder:30b",
        "messages": messages,
        "temperature": 0,
        "max_tokens": 1024,
        "stream": False,
    }
    if tools is not None:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    started = time.monotonic()
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=900) as response:
        raw = json.loads(response.read().decode())
    message = raw["choices"][0]["message"]
    return message, {
        "request_ms": round((time.monotonic() - started) * 1000, 3),
        "usage": raw.get("usage"),
        "finish_reason": raw["choices"][0].get("finish_reason"),
        "raw": raw,
    }


def write_fixture(root: Path, task: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "module.py").write_text(task["module"], encoding="utf-8")
    (root / "test_canary.py").write_text(task["test"], encoding="utf-8")


def run_test(root: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["python3", "test_canary.py"], cwd=root, text=True, capture_output=True, timeout=60
    )
    return {"exit_code": completed.returncode, "output": (completed.stdout + completed.stderr)[:30000]}


def action(root: Path, arguments: dict[str, Any]) -> str:
    kind = arguments.get("action")
    if kind == "read_file":
        path = arguments.get("path")
        if path not in {"module.py", "test_canary.py"}:
            raise ValueError("only module.py and test_canary.py can be read")
        return (root / path).read_text(encoding="utf-8")
    if kind == "write_file":
        if arguments.get("path") != "module.py" or not isinstance(arguments.get("content"), str):
            raise ValueError("only module.py may be written with string content")
        (root / "module.py").write_text(arguments["content"], encoding="utf-8")
        return "module.py written"
    if kind == "run_test":
        return json.dumps(run_test(root))
    raise ValueError("action is not allowed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=sorted(TASKS), required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8081/v1")
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--prepare-only", action="store_true", help="write a known failing fixture without inference")
    args = parser.parse_args()
    task = TASKS[args.task]
    root = args.workspace_root / args.task
    write_fixture(root, task)
    baseline = run_test(root)
    if args.prepare_only:
        print(json.dumps({"task": args.task, "workspace": str(root), "baseline": baseline}))
        return 0 if baseline["exit_code"] != 0 else 1
    if args.result is None:
        parser.error("--result is required unless --prepare-only is used")
    record: dict[str, Any] = {
        "started_at": stamp(), "task": args.task, "base_url": args.base_url,
        "baseline": baseline, "turns": [], "props_before": get_json(args.base_url.removesuffix("/v1") + "/props"),
        "metrics_before": get_text(args.base_url.removesuffix("/v1") + "/metrics"),
    }
    system = (
        "You are executing a fully specified local coding canary. Use no network, packages, shell, or paths outside the offered function. "
        "When tools are offered, make exactly one repository_action call per assistant turn."
    )
    readiness = (
        f"Task outcome: {task['outcome']} The only files are module.py and test_canary.py. "
        "The test command is exactly python3 test_canary.py. Do not edit or invoke tools now. "
        "Reply exactly READY if you have everything needed, otherwise MISSING followed by the precise missing item."
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": readiness}]
    ready, ready_meta = chat(args.base_url, messages, None)
    record["preflight"] = {"message": ready, **ready_meta}
    if (ready.get("content") or "").strip() != "READY" or ready.get("tool_calls"):
        record["result"] = "preflight_not_ready"
        record["finished_at"] = stamp()
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return 2
    messages.extend([ready, {"role": "user", "content": "Execute now: read both files, make the smallest correction to module.py, run the exact test command, and stop only after it passes."}])
    for number in range(1, args.max_turns + 1):
        reply, meta = chat(args.base_url, messages, [TOOL])
        calls = reply.get("tool_calls") or []
        turn: dict[str, Any] = {"number": number, "assistant": reply, **meta}
        record["turns"].append(turn)
        if len(calls) != 1:
            record["result"] = "invalid_tool_contract" if calls else "stopped_without_tool"
            break
        call = calls[0]
        if call.get("type") != "function" or call.get("function", {}).get("name") != "repository_action":
            record["result"] = "invalid_tool_contract"
            break
        arguments: dict[str, Any] = {}
        try:
            arguments = json.loads(call["function"]["arguments"])
            output = action(root, arguments)
        except Exception as exc:
            output = f"REJECTED: {type(exc).__name__}: {exc}"
            record["result"] = "rejected_action"
        turn["tool_output"] = output
        messages.extend([reply, {"role": "tool", "tool_call_id": call["id"], "content": output}])
        if arguments.get("action") == "run_test" and json.loads(output).get("exit_code") == 0:
            record["result"] = "passed"
            break
        if record.get("result") == "rejected_action":
            break
    else:
        record["result"] = "turn_limit"
    record["final_test"] = run_test(root)
    record["props_after"] = get_json(args.base_url.removesuffix("/v1") + "/props")
    record["metrics_after"] = get_text(args.base_url.removesuffix("/v1") + "/metrics")
    record["finished_at"] = stamp()
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return 0 if record["result"] == "passed" and record["final_test"]["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
