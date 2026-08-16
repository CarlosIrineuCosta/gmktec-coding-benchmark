from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_BASE = os.environ.get("BENCHMARK_OLLAMA_BASE", "http://gmktec:11434").rstrip("/")

TOOLS = [
    {"type": "function", "function": {"name": "list_files", "description": "List repository files", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a UTF-8 repository file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "search", "description": "Search repository text with ripgrep", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Create or replace a UTF-8 repository file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "run_command", "description": "Run a constrained test or inspection command in the repository", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
]

TEXT_TOOL_PROTOCOL = """
This model does not expose native tool calls. On every turn, respond with exactly
one JSON object and no markdown. To act, use
{"tool":"list_files|read_file|search|write_file|run_command","arguments":{...}}.
When the task is complete, use {"final":"brief completion summary"}.
Never claim a tool result before it is returned to you.
""".strip()


def ollama_json(method: str, path: str, payload=None, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(OLLAMA_BASE + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def unload(model: str, wait_seconds=60):
    try:
        ollama_json("POST", "/api/generate", {"model": model, "keep_alive": 0}, timeout=30)
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if not (ollama_json("GET", "/api/ps").get("models") or []): return True
            time.sleep(1)
    except Exception:
        return False
    return False


def wait_empty(wait_seconds: float) -> bool:
    deadline = time.monotonic() + max(0, wait_seconds)
    while time.monotonic() < deadline:
        try:
            if not (ollama_json("GET", "/api/ps").get("models") or []):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def run(model: str, prompt: str, worktree: Path, context: int, max_steps=80, max_seconds=1800):
    native_tools = not model.lower().startswith("medaibase/glm-4.6v-flash")
    system_prompt = "You are a coding agent. Work only through the supplied repository tools. Do not use network resources. Implement and test the task completely."
    if not native_tools:
        system_prompt += "\n\n" + TEXT_TOOL_PROTOCOL
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
    transcript = []
    totals = {"prompt_eval_count": 0, "eval_count": 0, "prompt_eval_duration": 0, "eval_duration": 0, "load_duration": 0, "tool_calls": 0, "command_failures": 0, "invalid_tool_calls": 0}
    final = ""
    deadline = time.monotonic() + max_seconds
    for step in range(max_steps):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return final, transcript, totals, "hard_timeout"
        payload = {
            "model": model, "messages": messages, "stream": False,
            "keep_alive": "30m", "options": {"num_ctx": context, "temperature": 0},
        }
        if native_tools:
            payload["tools"] = TOOLS
        try:
            response = ollama_json("POST", "/api/chat", payload, timeout=max(1, min(1800, remaining)))
        except TimeoutError:
            return final, transcript, totals, "hard_timeout"
        for key in ("prompt_eval_count", "eval_count", "prompt_eval_duration", "eval_duration", "load_duration"):
            totals[key] += int(response.get(key) or 0)
        message = response.get("message") or {}
        messages.append(message); transcript.append({"response": response})
        calls = message.get("tool_calls") or []
        if not native_tools:
            content = str(message.get("content") or "")
            try:
                parsed = _text_action(content)
            except (ValueError, json.JSONDecodeError) as exc:
                totals["invalid_tool_calls"] += 1
                transcript[-1]["invalid_action"] = f"{type(exc).__name__}: {exc}"
                messages.append({
                    "role": "user",
                    "content": "Your previous action was invalid JSON. Return exactly one valid JSON object matching the tool or final schema; do not use markdown.",
                })
                continue
            if "final" in parsed:
                return str(parsed["final"]), transcript, totals, str(response.get("done_reason") or "stop")
            calls = [{"function": {"name": parsed.get("tool", ""), "arguments": parsed.get("arguments") or {}}}]
        if not calls:
            final = str(message.get("content") or "")
            return final, transcript, totals, str(response.get("done_reason") or "stop")
        for call in calls:
            function = call.get("function") or {}; name = function.get("name", "")
            args = function.get("arguments") or {}
            if isinstance(args, str):
                try: args = json.loads(args)
                except ValueError: args = {}
            totals["tool_calls"] += 1
            try:
                output = _tool(name, args, worktree, deadline)
            except Exception as exc:
                output = f"ERROR {type(exc).__name__}: {exc}"
                totals["command_failures"] += 1
            if native_tools:
                messages.append({"role": "tool", "tool_name": name, "content": output[:20000]})
            else:
                messages.append({"role": "user", "content": f"Tool result for {name}:\n{output[:20000]}\n\nReturn the next single JSON action."})
    return final, transcript, totals, "max_tool_steps"


def _text_action(content: str) -> dict:
    value = content.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        value = "\n".join(lines[1:-1]).strip() if len(lines) >= 3 else value
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        start, end = value.find("{"), value.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("completion-only model returned no JSON action") from exc
        parsed = json.loads(value[start:end + 1])
    if not isinstance(parsed, dict) or not ({"tool", "final"} & parsed.keys()):
        raise ValueError("completion-only model returned an invalid JSON action")
    return parsed


def _path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if path != root.resolve() and root.resolve() not in path.parents:
        raise ValueError("path leaves repository")
    if ".git" in path.parts:
        raise ValueError("git internals are not accessible")
    return path


def _tool(name: str, args: dict, root: Path, deadline: float | None = None) -> str:
    if name == "list_files":
        base = _path(root, args.get("path", "."))
        return "\n".join(
            str(p.relative_to(root)) for p in sorted(base.rglob("*"))
            if p.is_file() and ".git" not in p.relative_to(root).parts
        )[:20000]
    if name == "read_file": return _path(root, args["path"]).read_text(encoding="utf-8")[:40000]
    if name == "search":
        base = _path(root, args.get("path", ".")); result = subprocess.run(["rg", "-n", "--", args["pattern"], str(base)], cwd=root, text=True, capture_output=True, timeout=30); return (result.stdout + result.stderr)[:20000]
    if name == "write_file":
        path = _path(root, args["path"]); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(args["content"], encoding="utf-8"); return f"wrote {len(args['content'])} characters"
    if name == "run_command":
        argv = shlex.split(args["command"])
        if not argv or argv[0] not in {"python", "python3", "pytest", "git", "rg", "sed", "find", "ls"}: raise ValueError("command is not allowed")
        if argv[0] == "git" and (len(argv) < 2 or argv[1] not in {"status", "diff", "log"}): raise ValueError("git operation is not allowed")
        remaining = 300 if deadline is None else max(1, min(300, deadline - time.monotonic()))
        result = subprocess.run(argv, cwd=root, text=True, capture_output=True, timeout=remaining, env={**os.environ, "PYTHONPATH": str(root / "src")})
        if result.returncode: raise RuntimeError(f"exit {result.returncode}\n{result.stdout}\n{result.stderr}")
        return (result.stdout + result.stderr)[:30000]
    raise ValueError("unknown tool")
