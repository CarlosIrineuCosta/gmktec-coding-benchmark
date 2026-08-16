"""Run a strict, local Ollama-vs-llama-server Qwen coding canary on GMKtec.

This deliberately uses one generic tool function. The executor rejects any
assistant turn that contains zero or more than one tool call, malformed JSON,
or an action outside the declared contract. Raw SSE chunks are retained before
tool parsing so backend/parser failures can be diagnosed without inference.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL = "qwen3-coder:30b"
OLLAMA_V1 = "http://127.0.0.1:11434/v1"
OLLAMA_API = "http://127.0.0.1:11434"
LLAMA_V1 = "http://127.0.0.1:8081/v1"
LLAMA_LAUNCH = Path("/home/cdc/llm/ab/llama-qwen3-coder-30b.sh")
QWEN_BLOB = Path(
    "/usr/share/ollama/.ollama/models/blobs/"
    "sha256-1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a"
)


def pytest_command() -> list[str]:
    """Use an explicitly provisioned canary interpreter when supplied."""
    return [os.environ.get("CANARY_PYTHON", "python3"), "-m", "pytest", "-q"]

TOOL = {
    "type": "function",
    "function": {
        "name": "repository_action",
        "description": "Perform exactly one permitted operation in the isolated task directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read_file", "write_file", "run_test"],
                },
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["action"],
        },
    },
}

SYSTEM = "You are a fully specified coding canary. Use only the supplied tool when tools are offered."
READINESS = (
    "This is an isolated two-file Python task. The required outcome is that "
    "normalize_tag strips surrounding whitespace and lowercases its input, with "
    "the supplied test passing. Make the smallest correction. No packages, network, "
    "or other tools are needed. Do not edit yet. Reply READY if this is sufficient, "
    "otherwise reply MISSING followed by the exact missing information."
)
EXECUTE = (
    "Execute now. On each assistant turn, make exactly one call to the single "
    "repository_action tool or finish only after the supplied test passes. First read "
    "module.py and test_module.py, then make the smallest edit, then run the test. "
    "Do not call a tool more than once in a turn."
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_request(url: str, body: dict[str, Any], timeout: int = 900) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def json_get(url: str, timeout: int = 30) -> dict[str, Any]:
    with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as response:
        return json.loads(response.read().decode())


def stream_chat(base_url: str, payload: dict[str, Any], timeout: int = 900) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return reconstructed assistant message and unparsed SSE evidence."""
    payload = {**payload, "stream": True}
    request = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    first_event_ms: float | None = None
    first_token_ms: float | None = None
    raw_events: list[str] = []
    content: list[str] = []
    tool_calls: dict[int, dict[str, Any]] = {}
    finish_reason: str | None = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or not line.startswith("data:"):
                continue
            event = line[5:].strip()
            raw_events.append(event)
            if event == "[DONE]":
                break
            if first_event_ms is None:
                first_event_ms = (time.monotonic() - started) * 1000
            try:
                chunk = json.loads(event)
            except json.JSONDecodeError:
                continue
            choice = (chunk.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}
            piece = delta.get("content")
            if piece:
                content.append(str(piece))
                first_token_ms = first_token_ms or (time.monotonic() - started) * 1000
            for call in delta.get("tool_calls") or []:
                index = int(call.get("index", 0))
                current = tool_calls.setdefault(
                    index,
                    {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                )
                current["id"] += str(call.get("id") or "")
                function = call.get("function") or {}
                current["function"]["name"] += str(function.get("name") or "")
                current["function"]["arguments"] += str(function.get("arguments") or "")
                first_token_ms = first_token_ms or (time.monotonic() - started) * 1000
            finish_reason = choice.get("finish_reason") or finish_reason
    return (
        {"role": "assistant", "content": "".join(content), "tool_calls": list(tool_calls.values())},
        {
            "raw_sse": raw_events,
            "first_event_latency_ms": first_event_ms,
            "first_token_latency_ms": first_token_ms,
            "finish_reason": finish_reason,
            "response_duration_ms": (time.monotonic() - started) * 1000,
        },
    )


def reset_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "module.py").write_text(
        'def normalize_tag(value: str) -> str:\n'
        '    """Return a normalized tag without surrounding whitespace."""\n'
        '    return value.lower()\n',
        encoding="utf-8",
    )
    (root / "test_module.py").write_text(
        'from module import normalize_tag\n\n\n'
        'def test_normalize_tag_strips_and_lowercases():\n'
        '    assert normalize_tag("  Urgent  ") == "urgent"\n',
        encoding="utf-8",
    )


def safe_path(root: Path, value: str) -> Path:
    target = (root / value).resolve()
    if target != root.resolve() and root.resolve() not in target.parents:
        raise ValueError("path leaves task directory")
    return target


def execute_action(root: Path, arguments: dict[str, Any]) -> str:
    action = arguments.get("action")
    if action == "read_file":
        path = arguments.get("path")
        if path not in {"module.py", "test_module.py"}:
            raise ValueError("read path is not permitted")
        return safe_path(root, path).read_text(encoding="utf-8")
    if action == "write_file":
        if arguments.get("path") != "module.py" or not isinstance(arguments.get("content"), str):
            raise ValueError("only module.py may be written with string content")
        safe_path(root, "module.py").write_text(arguments["content"], encoding="utf-8")
        return "module.py written"
    if action == "run_test":
        result = subprocess.run(pytest_command(), cwd=root, text=True, capture_output=True, timeout=60)
        return f"exit={result.returncode}\n{result.stdout}{result.stderr}"[:30000]
    raise ValueError("action is not permitted")


def final_test(root: Path) -> dict[str, Any]:
    result = subprocess.run(pytest_command(), cwd=root, text=True, capture_output=True, timeout=60)
    return {"exit_code": result.returncode, "output": result.stdout + result.stderr}


class Monitor:
    def __init__(self, pids: list[int]):
        self.pids = pids
        self.samples: list[dict[str, Any]] = []
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=2)

    def _run(self) -> None:
        while not self.stop.is_set():
            sample: dict[str, Any] = {"at": time.monotonic(), "rss_kib": {}}
            try:
                for line in Path("/proc/meminfo").read_text().splitlines():
                    if line.startswith("MemAvailable:"):
                        sample["mem_available_kib"] = int(line.split()[1])
            except OSError:
                pass
            for pid in self.pids:
                try:
                    fields = Path(f"/proc/{pid}/status").read_text().splitlines()
                    rss = next(line for line in fields if line.startswith("VmRSS:"))
                    sample["rss_kib"][str(pid)] = int(rss.split()[1])
                except (OSError, StopIteration):
                    pass
            self.samples.append(sample)
            self.stop.wait(0.2)

    def summary(self) -> dict[str, Any]:
        return {
            "minimum_mem_available_kib": min((x.get("mem_available_kib", 0) for x in self.samples), default=0),
            "peak_rss_kib": {
                pid: max((x.get("rss_kib", {}).get(pid, 0) for x in self.samples), default=0)
                for pid in {p for x in self.samples for p in x.get("rss_kib", {})}
            },
            "sample_count": len(self.samples),
        }


def server_pids(pattern: str) -> list[int]:
    result = subprocess.run(["pgrep", "-f", pattern], text=True, capture_output=True)
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def wait_health(base_url: str, timeout: int = 600) -> None:
    deadline = time.monotonic() + timeout
    last_error = "not attempted"
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(base_url + "/health")
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 200:
                    return
        except Exception as exc:  # health endpoint is expected to return 503 while loading
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(1)
    raise RuntimeError(f"server did not become healthy: {last_error}")


def props(base_url: str) -> dict[str, Any] | None:
    try:
        request = urllib.request.Request(base_url.removesuffix("/v1") + "/props")
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None


def effective_context(backend: "Backend") -> dict[str, Any] | None:
    if backend.name == "llama-server":
        return props(backend.base_url)
    try:
        payload = json_get(OLLAMA_API + "/api/ps", timeout=10)
        return next((row for row in payload.get("models") or [] if row.get("name") == MODEL), None)
    except Exception:
        return None


def ollama_unload() -> None:
    try:
        json_request(OLLAMA_API + "/api/generate", {"model": MODEL, "keep_alive": 0}, timeout=30)
    except Exception:
        pass


def ollama_warm(context: int) -> float:
    started = time.monotonic()
    json_request(
        OLLAMA_API + "/api/chat",
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": "Reply READY."}],
            "stream": False,
            "keep_alive": "30m",
            "think": False,
            "options": {"num_ctx": context, "num_predict": 16, "temperature": 0},
        },
    )
    return time.monotonic() - started


@dataclass
class Backend:
    name: str
    base_url: str
    launch: subprocess.Popen[str] | None = None
    load_seconds: float | None = None

    def start(self, context: int, log_path: Path) -> None:
        if self.name == "ollama":
            ollama_unload()
            self.load_seconds = ollama_warm(context)
            return
        environment = {**os.environ, "LLAMA_CTX_SIZE": str(context), "LLAMA_N_PREDICT": "1024"}
        log_file = log_path.open("w", encoding="utf-8")
        started = time.monotonic()
        self.launch = subprocess.Popen([str(LLAMA_LAUNCH)], stdout=log_file, stderr=subprocess.STDOUT, text=True, env=environment)
        try:
            wait_health(self.base_url)
            self.load_seconds = time.monotonic() - started
        except Exception:
            self.stop()
            raise

    def stop(self) -> None:
        if self.name == "ollama":
            ollama_unload()
            return
        if self.launch and self.launch.poll() is None:
            self.launch.send_signal(signal.SIGTERM)
            try:
                self.launch.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.launch.kill()
                self.launch.wait(timeout=10)


def run_once(backend: Backend, root: Path, context: int, repetition: int) -> dict[str, Any]:
    reset_fixture(root)
    transcript: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": READINESS},
    ]
    request_base = {"model": MODEL, "temperature": 0, "max_tokens": 1024, "parallel_tool_calls": False}
    started_at = now()
    started = time.monotonic()
    pids = server_pids("ollama serve") if backend.name == "ollama" else ([backend.launch.pid] if backend.launch else [])
    stop_reason = "max_steps"
    test_passed_in_loop = False
    with Monitor(pids) as monitor:
        try:
            readiness, evidence = stream_chat(backend.base_url, request_base | {"messages": messages})
            transcript.append({"phase": "readiness", "message": readiness, "transport": evidence})
            messages.append(readiness)
            messages.append({"role": "user", "content": EXECUTE})
            for step in range(10):
                request_payload = request_base | {"messages": messages}
                if not test_passed_in_loop:
                    request_payload["tools"] = [TOOL]
                reply, evidence = stream_chat(backend.base_url, request_payload)
                transcript.append({"phase": "execution", "step": step + 1, "message": reply, "transport": evidence})
                calls = reply.get("tool_calls") or []
                if test_passed_in_loop:
                    if calls:
                        stop_reason = "tool_call_after_tools_removed"
                    else:
                        stop_reason = evidence.get("finish_reason") or "final_after_passing_test"
                    break
                if not calls:
                    stop_reason = evidence.get("finish_reason") or "no_tool_call"
                    break
                if len(calls) != 1:
                    stop_reason = "multiple_tool_calls_rejected"
                    break
                call = calls[0]
                function = call.get("function") or {}
                if function.get("name") != "repository_action":
                    stop_reason = "unexpected_tool_rejected"
                    break
                try:
                    arguments = json.loads(function.get("arguments") or "{}")
                    if not isinstance(arguments, dict):
                        raise ValueError("arguments must be an object")
                    output = execute_action(root, arguments)
                except Exception as exc:
                    stop_reason = "malformed_or_disallowed_tool_rejected"
                    transcript[-1]["tool_error"] = f"{type(exc).__name__}: {exc}"
                    break
                messages.append(reply)
                messages.append({"role": "tool", "tool_call_id": call.get("id") or "call_0", "content": output})
                if arguments.get("action") == "run_test" and output.startswith("exit=0\n"):
                    test_passed_in_loop = True
            test = final_test(root)
        except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
            stop_reason = f"transport_or_harness_error:{type(exc).__name__}"
            test = final_test(root)
            transcript.append({"phase": "harness_error", "error": f"{type(exc).__name__}: {exc}"})
        resource = monitor.summary()
    module = (root / "module.py").read_text(encoding="utf-8")
    return {
        "schema_version": "0.1.0",
        "run_id": f"{backend.name}__qwen3-coder-30b__ctx{context}__rep{repetition}",
        "started_at": started_at,
        "finished_at": now(),
        "backend": {
            "name": backend.name,
            "base_url": backend.base_url,
            "load_seconds": backend.load_seconds,
            "llama_cpp_commit": "4df29be4f4c3673f428170fda944a5b19f743bb8" if backend.name == "llama-server" else None,
            "server_command": [str(LLAMA_LAUNCH), "LLAMA_CTX_SIZE=<context>"] if backend.name == "llama-server" else None,
            "ollama_options": {"num_ctx": context, "num_predict": 1024, "temperature": 0} if backend.name == "ollama" else None,
        },
        "model": {
            "identifier": MODEL,
            "gguf_path": str(QWEN_BLOB),
            "digest": QWEN_BLOB.name.removeprefix("sha256-"),
            "byte_size": QWEN_BLOB.stat().st_size,
        },
        "context": {"requested_tokens": context, "effective_context_evidence": effective_context(backend)},
        "sampling": {"temperature": 0, "max_tokens": 1024, "stream": True, "parallel_tool_calls": False},
        "contract": {"single_tool_function": TOOL, "raw_output_retained": True},
        "outcome": {"stop_reason": stop_reason, "test": test, "module": module, "wall_seconds": time.monotonic() - started},
        "resources": resource,
        "transcript": transcript,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--fixture-dir", type=Path, required=True)
    parser.add_argument("--contexts", type=int, nargs="+", default=[8192, 16384, 32768])
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    # The host-side sha256sum verification is recorded in the manifest. Avoid
    # rereading 18 GiB before every experiment merely to recompute it here.
    if not QWEN_BLOB.is_file() or QWEN_BLOB.stat().st_size != 18_556_688_736:
        raise SystemExit("pinned Qwen GGUF is missing or has an unexpected size")
    for context in args.contexts:
        condition_ok = True
        for name, base_url in (("ollama", OLLAMA_V1), ("llama-server", LLAMA_V1)):
            backend = Backend(name, base_url)
            try:
                backend.start(context, args.results_dir / f"{name}__ctx{context}.server.log")
                for repetition in range(1, args.repetitions + 1):
                    record = run_once(backend, args.fixture_dir, context, repetition)
                    path = args.results_dir / f"{record['run_id']}.json"
                    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
                    if record["outcome"]["test"]["exit_code"] != 0 or record["outcome"]["stop_reason"] not in {"stop", "length"}:
                        condition_ok = False
            finally:
                backend.stop()
        if not condition_ok:
            raise SystemExit(f"context {context} failed; higher contexts were not run")


if __name__ == "__main__":
    main()
