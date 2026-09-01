"""One direct, tool-free operational-v1 inference request per invocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .fixtures import fixture
from .prompts import prompt
from .score import score
from .telemetry import TelemetrySampler

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "private" / "results" / "operational_v1"
TASKS = ("classification", "extraction", "docs_qa", "report", "patch")
OUTPUT_LIMITS = {"classification": 1600, "extraction": 2400, "docs_qa": 2000, "report": 1500, "patch": 1500}


def utcnow() -> str: return datetime.now(timezone.utc).isoformat()


def output_limit(task_id: str) -> int: return OUTPUT_LIMITS[task_id]


def request(endpoint: str, model: str, task_id: str, context: int, timeout: int) -> tuple[str, dict]:
    body = {"model": model, "messages": [{"role": "user", "content": prompt(task_id)}], "temperature": 0, "max_tokens": output_limit(task_id), "stream": True, "stream_options": {"include_usage": True}, "options": {"num_ctx": context, "temperature": 0}}
    raw = json.dumps(body).encode(); started = time.monotonic()
    req = urllib.request.Request(endpoint.rstrip("/") + "/chat/completions", data=raw, headers={"Content-Type": "application/json"})
    chunks: list[str] = []; first_token_ms = None; stop_reason = None; usage = None; response_id = None; malformed_events = 0
    with urllib.request.urlopen(req, timeout=timeout) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"): continue
            value = line[5:].strip()
            if value == "[DONE]": break
            try:
                payload = json.loads(value)
            except json.JSONDecodeError:
                malformed_events += 1
                continue
            response_id = response_id or payload.get("id"); usage = payload.get("usage") or usage
            choice = (payload.get("choices") or [{}])[0]; delta = choice.get("delta") or {}
            token = delta.get("content") or delta.get("reasoning_content")
            if token:
                first_token_ms = first_token_ms or round((time.monotonic() - started) * 1000, 3); chunks.append(str(delta.get("content") or ""))
            stop_reason = choice.get("finish_reason") or stop_reason
    return "".join(chunks), {"wall_seconds": round(time.monotonic() - started, 3), "first_token_latency_ms": first_token_ms, "stop_reason": stop_reason, "usage": usage, "response_id": response_id, "malformed_sse_events": malformed_events}


def run_one(args) -> dict:
    packet = prompt(args.task); run_id = f"opv1-{args.slug}-{args.task}-{datetime.now().strftime('%H%M%S')}"
    dest = RESULTS / args.slug / args.task / run_id; dest.mkdir(parents=True, exist_ok=False)
    record = {"run_id": run_id, "stage": "operational_v1", "started_at": utcnow(), "model": {"identifier": args.model, "digest": args.digest, "quantization": args.quantization, "template": args.template}, "backend": {"endpoint": args.endpoint, "identity": args.backend, "version": args.backend_version}, "task": args.task, "context_requested": args.context, "temperature": 0, "max_output_tokens": output_limit(args.task), "packet_sha256": hashlib.sha256(packet.encode()).hexdigest(), "fixture_sha256": hashlib.sha256(json.dumps(fixture(args.task), sort_keys=True).encode()).hexdigest(), "status": "serving_failure"}
    sampler = TelemetrySampler(args.server_pid, args.telemetry_interval)
    sampler.start()
    try:
        answer, metrics = request(args.endpoint, args.model, args.task, args.context, args.timeout)
        (dest / "raw-answer.txt").write_text(answer, encoding="utf-8")
        record.update(status="completed", metrics=metrics, score=score(args.task, answer, dest / "score.json"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        record["error"] = {"type": type(exc).__name__, "message": str(exc)[:1000]}
    finally:
        telemetry_summary = sampler.stop()
        sampler.write(dest / "telemetry.json", telemetry_summary)
        record["telemetry"] = {"path": "telemetry.json", "summary": telemetry_summary}
    record["finished_at"] = utcnow(); (dest / "run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("run_id", "status", "model", "task", "metrics", "score", "error") if key in record}, indent=2)); return record


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--model", required=True); parser.add_argument("--slug", required=True); parser.add_argument("--digest", required=True); parser.add_argument("--quantization", required=True); parser.add_argument("--template", default="unknown"); parser.add_argument("--task", choices=TASKS, required=True); parser.add_argument("--endpoint", default="http://127.0.0.1:8081/v1"); parser.add_argument("--backend", default="llama-server"); parser.add_argument("--backend-version", default="unknown"); parser.add_argument("--context", type=int, default=16384); parser.add_argument("--timeout", type=int, default=900); parser.add_argument("--server-pid", type=int); parser.add_argument("--telemetry-interval", type=float, default=1.0)
    run_one(parser.parse_args())


if __name__ == "__main__": main()
