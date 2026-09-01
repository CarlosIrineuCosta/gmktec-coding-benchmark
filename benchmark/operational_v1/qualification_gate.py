"""Disposable serving and tool gate for one locally stored GGUF artifact."""
from __future__ import annotations

import argparse
import json
import re
import signal
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .telemetry import TelemetrySampler


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stream_request(endpoint: str, body: dict[str, Any], timeout: int) -> tuple[str, dict[str, Any], dict[str, Any]]:
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps({**body, "stream": True, "stream_options": {"include_usage": True}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    first_token: float | None = None
    chunks: list[str] = []
    events: list[dict[str, Any]] = []
    usage: dict[str, Any] | None = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            event = line[5:].strip()
            if event == "[DONE]":
                break
            try:
                payload = json.loads(event)
            except json.JSONDecodeError:
                continue
            events.append(payload)
            usage = payload.get("usage") or usage
            choice = (payload.get("choices") or [{}])[0]
            content = (choice.get("delta") or {}).get("content") or ""
            if content:
                first_token = first_token or (time.monotonic() - started)
                chunks.append(content)
    elapsed = time.monotonic() - started
    completion = usage.get("completion_tokens") if isinstance(usage, dict) else None
    metrics = {
        "wall_seconds": round(elapsed, 3),
        "first_token_latency_seconds": round(first_token, 3) if first_token is not None else None,
        "usage": usage,
        "decode_tokens_per_second": round(completion / max(elapsed - (first_token or 0), 0.001), 3) if isinstance(completion, int) else None,
    }
    return "".join(chunks), metrics, {"events": events}


def json_request(endpoint: str, body: dict[str, Any], timeout: int) -> tuple[dict[str, Any], dict[str, Any]]:
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload, {"wall_seconds": round(time.monotonic() - started, 3), "usage": payload.get("usage")}


def parse_adapter_action(content: str) -> dict[str, Any] | None:
    """Accept one explicit JSON action, optionally inside a tool_call tag."""
    match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", content, flags=re.DOTALL)
    candidate = match.group(1) if match else content.strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or not isinstance(value.get("name"), str) or not isinstance(value.get("arguments"), dict):
        return None
    return value


def tool_result(response: dict[str, Any], mode: str) -> dict[str, Any]:
    message = ((response.get("choices") or [{}])[0].get("message") or {})
    action: dict[str, Any] | None = None
    if mode == "native_openai":
        calls = message.get("tool_calls") or []
        if len(calls) == 1:
            function = calls[0].get("function") or {}
            try:
                arguments = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = None
            if isinstance(arguments, dict):
                action = {"name": function.get("name"), "arguments": arguments}
    else:
        action = parse_adapter_action(str(message.get("content") or ""))
    valid = bool(action and action.get("name") == "read_fixture" and action.get("arguments", {}).get("path") == "canary.txt")
    return {"mode": mode, "parsed_action": action, "bounded_action_succeeded": valid, "bounded_result": "qualification-token" if valid else None}


def wait_for_health(endpoint: str, process: subprocess.Popen[str], deadline_seconds: int) -> tuple[bool, float]:
    started = time.monotonic()
    health = endpoint.removesuffix("/v1") + "/health"
    while time.monotonic() - started < deadline_seconds:
        if process.poll() is not None:
            return False, time.monotonic() - started
        try:
            with urllib.request.urlopen(health, timeout=3) as response:
                if response.status == 200:
                    return True, time.monotonic() - started
        except OSError:
            pass
        time.sleep(1)
    return False, time.monotonic() - started


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one disposable local-model qualification gate")
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--quantization", required=True)
    parser.add_argument("--artifact-sha256", required=True)
    parser.add_argument("--server", required=True, type=Path)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--context", required=True, type=int)
    parser.add_argument("--reasoning", choices=("on", "off", "auto"), default="auto")
    parser.add_argument("--reasoning-effort", default="default")
    parser.add_argument("--tool-mode", choices=("native_openai", "structured_adapter"), required=True)
    parser.add_argument("--tool-format-note", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if not args.model_path.is_file() or not args.server.is_file():
        raise FileNotFoundError("model artifact or llama-server is unavailable")
    run_dir = args.evidence_root / args.slug / f"gate-{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"
    run_dir.mkdir(parents=True, exist_ok=False)
    endpoint = f"http://127.0.0.1:{args.port}/v1"
    command = [
        str(args.server), "--model", str(args.model_path), "--host", "127.0.0.1", "--port", str(args.port),
        "--ctx-size", str(args.context), "--gpu-layers", "999", "--flash-attn", "on", "--jinja",
        "--reasoning", args.reasoning, "--reasoning-effort", args.reasoning_effort, "--metrics", "--no-webui",
    ]
    write_json(run_dir / "spec.json", {
        "schema_version": 1, "started_at": utcnow(), "model": args.model, "revision": args.revision,
        "quantization": args.quantization, "artifact_path": str(args.model_path), "artifact_sha256": args.artifact_sha256,
        "endpoint": endpoint, "context": args.context, "reasoning": args.reasoning,
        "reasoning_effort": args.reasoning_effort, "tool_mode": args.tool_mode, "tool_format_note": args.tool_format_note,
        "server_command": command,
    })
    server_log = run_dir / "server.log"
    with server_log.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, text=True)
        sampler = TelemetrySampler(process.pid)
        sampler.start()
        terminal: dict[str, Any] = {"status": "serving_failure"}
        try:
            healthy, load_seconds = wait_for_health(endpoint, process, args.timeout)
            if not healthy:
                terminal["reason"] = "llama-server did not become healthy"
            else:
                serving_answer, serving_metrics, raw = stream_request(endpoint, {
                    "model": args.model, "messages": [{"role": "user", "content": "Reply with exactly CANARY_OK and nothing else."}],
                    "temperature": 0, "max_tokens": 512,
                }, args.timeout)
                write_json(run_dir / "serving-response.json", raw)
                (run_dir / "serving-answer.txt").write_text(serving_answer, encoding="utf-8")
                serving_ok = serving_answer.strip() == "CANARY_OK"
                native_tools = [{"type": "function", "function": {"name": "read_fixture", "description": "Read the fixed token file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}}]
                if args.tool_mode == "native_openai":
                    tool_body = {"model": args.model, "messages": [{"role": "user", "content": "Call read_fixture exactly once with path canary.txt. Do not explain."}], "tools": native_tools, "tool_choice": "auto", "temperature": 0, "max_tokens": 256}
                else:
                    tool_body = {"model": args.model, "messages": [{"role": "user", "content": "Return only <tool_call>{\"name\":\"read_fixture\",\"arguments\":{\"path\":\"canary.txt\"}}</tool_call> for this bounded tool task."}], "temperature": 0, "max_tokens": 256}
                tool_response, tool_metrics = json_request(endpoint, tool_body, args.timeout)
                write_json(run_dir / "tool-response.json", tool_response)
                parsed = tool_result(tool_response, args.tool_mode)
                write_json(run_dir / "tool-canary.json", {**parsed, "request_metrics": tool_metrics})
                terminal = {
                    "status": "passed" if serving_ok and parsed["bounded_action_succeeded"] else "configuration_tool_compatibility_blocked",
                    "serving_canary": "pass" if serving_ok else "fail", "tool_canary": "pass" if parsed["bounded_action_succeeded"] else "fail",
                    "serving_metrics": serving_metrics, "tool_metrics": tool_metrics, "load_seconds": round(load_seconds, 3),
                }
        except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
            terminal = {"status": "serving_failure", "reason": f"{type(exc).__name__}: {exc}"}
        finally:
            summary = sampler.stop()
            sampler.write(run_dir / "telemetry.json", summary)
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=30)
    terminal["finished_at"] = utcnow()
    terminal["telemetry"] = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))["summary"]
    write_json(run_dir / "terminal.json", terminal)
    print(json.dumps({"run_dir": str(run_dir), **terminal}, indent=2))
    return 0 if terminal["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
