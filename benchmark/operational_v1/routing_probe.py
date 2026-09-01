"""One new synthetic patch probe for a telemetry-backed routing decision."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .run import ROOT
from .telemetry import TelemetrySampler

TASK_ROOT = ROOT / "tasks" / "routing-probe-2026-09-01"
RESULTS = ROOT / "data" / "private" / "results" / "routing_probe"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def packet() -> str:
    source = (TASK_ROOT / "retry.py").read_text(encoding="utf-8")
    task = (TASK_ROOT / "PACKET.md").read_text(encoding="utf-8")
    return f"{task}\n\nFILE retry.py:\n```python\n{source}```\n"


def request(endpoint: str, model: str, timeout: int) -> tuple[str, dict[str, Any]]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": packet()}],
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "max_tokens": 4096,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    started = time.monotonic()
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    chunks: list[str] = []
    first_token_ms: float | None = None
    usage = None
    stop_reason = None
    malformed_events = 0
    with urllib.request.urlopen(req, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            event = line[5:].strip()
            if event == "[DONE]":
                break
            try:
                payload = json.loads(event)
            except json.JSONDecodeError:
                malformed_events += 1
                continue
            usage = payload.get("usage") or usage
            choice = (payload.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}
            content = delta.get("content") or ""
            if content:
                first_token_ms = first_token_ms or round((time.monotonic() - started) * 1000, 3)
                chunks.append(content)
            stop_reason = choice.get("finish_reason") or stop_reason
    return "".join(chunks), {
        "wall_seconds": round(time.monotonic() - started, 3),
        "first_token_latency_ms": first_token_ms,
        "stop_reason": stop_reason,
        "usage": usage,
        "malformed_sse_events": malformed_events,
    }


def evaluate(answer: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="routing-probe-") as raw:
        root = Path(raw)
        for name in ("retry.py", "test_retry.py"):
            shutil.copy2(TASK_ROOT / name, root / name)
        patch_text = answer.strip()
        if patch_text.startswith("```diff") and patch_text.endswith("```"):
            patch_text = "\n".join(patch_text.splitlines()[1:-1]).strip()
        strip = 1 if patch_text.startswith("--- a/") or patch_text.startswith("diff --git a/") else 0
        patch = subprocess.run(["patch", f"-p{strip}", "--batch"], cwd=root, input=patch_text + "\n", text=True, capture_output=True, timeout=30)
        test = subprocess.run(["python3", "-m", "unittest", "-v"], cwd=root, text=True, capture_output=True, timeout=60) if patch.returncode == 0 else None
        return {
            "patch_exit_code": patch.returncode,
            "patch_strip_level": strip,
            "patch_output": (patch.stdout + patch.stderr)[-4000:],
            "test_exit_code": test.returncode if test else None,
            "test_output": (test.stdout + test.stderr)[-4000:] if test else "",
            "accepted": bool(test and test.returncode == 0),
        }


def run(args: argparse.Namespace) -> dict[str, Any]:
    run_id = f"routing-probe-{args.slug}-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    destination = RESULTS / args.slug / run_id
    destination.mkdir(parents=True, exist_ok=False)
    prompt = packet()
    record: dict[str, Any] = {
        "run_id": run_id,
        "stage": "routing_probe_2026_09_01",
        "started_at": utcnow(),
        "model": {"identifier": args.model, "revision": args.revision, "quantization": args.quantization, "model_sha256": args.model_sha256},
        "backend": {
            "endpoint": args.endpoint,
            "version": args.backend_version,
            "context": args.context,
            "reasoning": args.reasoning,
            "reasoning_effort": args.reasoning_effort,
            "reasoning_preserve": args.reasoning_preserve,
        },
        "request": {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0, "max_tokens": 4096, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()},
        "server_lifecycle_telemetry": args.server_lifecycle_telemetry,
        "status": "serving_failure",
    }
    (destination / "prompt.md").write_text(prompt, encoding="utf-8")
    sampler = TelemetrySampler(args.server_pid, args.telemetry_interval)
    sampler.start()
    try:
        answer, metrics = request(args.endpoint, args.model, args.timeout)
        (destination / "raw-answer.txt").write_text(answer, encoding="utf-8")
        record.update(status="completed", metrics=metrics, acceptance=evaluate(answer))
    except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        record["error"] = {"type": type(exc).__name__, "message": str(exc)[:1000]}
    finally:
        summary = sampler.stop()
        sampler.write(destination / "telemetry.json", summary)
        record["telemetry"] = {"path": "telemetry.json", "summary": summary}
    record["finished_at"] = utcnow()
    (destination / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("run_id", "status", "metrics", "acceptance", "telemetry", "error") if key in record}, indent=2))
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--quantization", required=True)
    parser.add_argument("--model-sha256", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--backend-version", required=True)
    parser.add_argument("--context", type=int, default=65536)
    parser.add_argument("--reasoning", choices=("on", "off", "auto"), default="auto")
    parser.add_argument("--reasoning-effort", default="default")
    parser.add_argument("--reasoning-preserve", action="store_true")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--server-pid", type=int, required=True)
    parser.add_argument("--telemetry-interval", type=float, default=1.0)
    parser.add_argument("--server-lifecycle-telemetry")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
