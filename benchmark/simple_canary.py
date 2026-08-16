from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path


BASE_URL = "http://gmktec:11434"
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read one UTF-8 file from the isolated task directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Replace one UTF-8 file in the isolated task directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_test",
            "description": "Run the supplied pytest test. This tool accepts no arguments.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def chat(model: str, messages: list[dict], *, tools: bool) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": {"num_ctx": 8192, "num_predict": 1024, "temperature": 0},
    }
    if tools:
        payload["tools"] = TOOLS
    request = urllib.request.Request(
        BASE_URL + "/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.loads(response.read().decode())


def safe_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if root.resolve() != path and root.resolve() not in path.parents:
        raise ValueError("path leaves isolated task directory")
    return path


def execute_tool(root: Path, call: dict) -> str:
    function = call.get("function") or {}
    name = function.get("name")
    arguments = function.get("arguments") or {}
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    if name == "read_file":
        return safe_path(root, arguments["path"]).read_text(encoding="utf-8")
    if name == "write_file":
        safe_path(root, arguments["path"]).write_text(arguments["content"], encoding="utf-8")
        return "file written"
    if name == "run_test":
        result = subprocess.run(
            ["python3", "-m", "pytest", "-q"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=60,
        )
        return f"exit={result.returncode}\n{result.stdout}{result.stderr}"
    raise ValueError(f"unknown tool: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    contract = (
        "This is an isolated two-file Python task. Inspect module.py and test_module.py. "
        "The required outcome is that normalize_tag strips surrounding whitespace and "
        "lowercases its input, with the supplied test passing. Make the smallest correction. "
        "You will have exactly read_file, write_file, and run_test; no packages, network, or "
        "other tools are needed. Deliver the corrected module.py and a passing test. "
        "Do not edit yet. Reply READY if this is sufficient, otherwise reply MISSING followed "
        "by the exact missing information."
    )
    messages = [
        {"role": "system", "content": "You are performing a fully specified coding canary."},
        {"role": "user", "content": contract},
    ]
    started = time.monotonic()
    readiness = chat(args.model, messages, tools=False)
    ready_message = readiness.get("message") or {}
    messages.append(ready_message)
    messages.append({
        "role": "user",
        "content": (
            "Execute now. Use the supplied tools, at most one tool call per turn. "
            "Read both files, make the minimal edit, run the test, and report only after it passes."
        ),
    })
    transcript = [{"phase": "readiness", "response": readiness}]
    stop_reason = "max_steps"
    for _ in range(10):
        response = chat(args.model, messages, tools=True)
        message = response.get("message") or {}
        messages.append(message)
        transcript.append({"phase": "execution", "response": response})
        calls = message.get("tool_calls") or []
        if not calls:
            stop_reason = response.get("done_reason") or "no_tool_call"
            break
        for call in calls:
            try:
                output = execute_tool(args.worktree, call)
            except Exception as exc:
                output = f"ERROR {type(exc).__name__}: {exc}"
            messages.append({
                "role": "tool",
                "tool_name": (call.get("function") or {}).get("name", ""),
                "content": output,
            })

    test = subprocess.run(
        ["python3", "-m", "pytest", "-q"],
        cwd=args.worktree,
        text=True,
        capture_output=True,
        timeout=60,
    )
    result = {
        "model": args.model,
        "context": 8192,
        "readiness": ready_message.get("content", ""),
        "stop_reason": stop_reason,
        "wall_seconds": time.monotonic() - started,
        "test_exit_code": test.returncode,
        "test_output": test.stdout + test.stderr,
        "module": (args.worktree / "module.py").read_text(encoding="utf-8"),
        "transcript": transcript,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "model", "context", "readiness", "stop_reason", "wall_seconds",
        "test_exit_code", "test_output", "module",
    )}, indent=2))


if __name__ == "__main__":
    main()
