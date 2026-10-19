"""Comparable local OpenAI-compatible endpoint probe (Python standard library).

Records raw output and timings; makes no automatic claim about coding quality.
Run only against an endpoint you control. Results may contain source text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REVIEW_SOURCE = '''def claim(job_id, lease_until, now, attempts):
    if job_id in attempts:
        return attempts[job_id]
    if now > lease_until:
        return None
    attempts[job_id] = {"state": "claimed", "at": now}
    return attempts[job_id]

def deliver(event, sent_ids, send):
    if event["correlation_id"] in sent_ids:
        return "already sent"
    send(event["payload"])
    sent_ids.add(event["correlation_id"])
    return "sent"
'''

CASES = {
    "coding": (
        "Review the following Python code for two concrete correctness or replay defects. "
        "Return a short explanation with a suggested fix for each; do not execute code.\n\n"
        + REVIEW_SOURCE
    ),
    "copy": (
        "Repeat the following passage exactly, with no preface:\n\n"
        + ("Event 17 belongs to source A; its receipt is not evidence for source B.\n" * 40)
    ),
}


def request_json(url: str, *, payload: dict | None = None, timeout: int = 600):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def run_case(base: str, model: str, prompt: str, max_tokens: int, timeout: int) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    req = urllib.request.Request(
        base + "/chat/completions", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    start = time.perf_counter()
    first = None
    pieces = []
    reasoning = []
    usage = None
    timings = None
    finish_reason = None
    with urllib.request.urlopen(req, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[6:])
            if chunk.get("usage"):
                usage = chunk["usage"]
            if chunk.get("timings"):
                timings = chunk["timings"]
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                content = delta.get("content") or ""
                thought = delta.get("reasoning_content") or ""
                if content or thought:
                    if first is None:
                        first = time.perf_counter()
                    pieces.append(content)
                    reasoning.append(thought)
                finish_reason = choice.get("finish_reason") or finish_reason
    end = time.perf_counter()
    completion = usage.get("completion_tokens") if usage else None
    decode_seconds = end - first if first else None
    return {
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_chars": len(prompt), "output": "".join(pieces),
        "reasoning": "".join(reasoning), "usage": usage, "timings": timings,
        "finish_reason": finish_reason,
        "wall_seconds": round(end - start, 3),
        "first_token_seconds": round(first - start, 3) if first else None,
        "decode_seconds_approx": round(decode_seconds, 3) if decode_seconds else None,
        "completion_tokens_per_wall_second": round(completion / (end - start), 2) if completion else None,
        "completion_tokens_per_decode_second_approx": round(completion / decode_seconds, 2)
        if completion and decode_seconds and decode_seconds > 0 else None,
    }


def gpu_snapshot():
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,uuid,memory.total,memory.used,power.draw,temperature.gpu",
             "--format=csv,noheader"], capture_output=True, text=True, timeout=10, check=True,
        )
        return r.stdout.strip().splitlines()
    except (OSError, subprocess.SubprocessError):
        return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://127.0.0.1:18080/v1")
    p.add_argument("--model", help="served model ID; default: first /v1/models entry")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--repeat", type=int, default=3)
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--prompt-file", type=Path, help="additional private, realistic coding prompt")
    args = p.parse_args()
    if args.repeat < 1 or args.max_tokens < 1:
        p.error("repeat and max-tokens must be positive")
    base = args.base_url.rstrip("/")
    if not base.endswith("/v1"):
        p.error("base-url must end with /v1")
    models = request_json(base + "/models", timeout=15)
    available = [row["id"] for row in models.get("data", [])]
    if not available:
        raise RuntimeError("no served model found at /v1/models")
    model = args.model or available[0]
    if model not in available:
        raise RuntimeError(f"model {model!r} not advertised; available: {available}")
    cases = dict(CASES)
    if args.prompt_file:
        cases["real_coding"] = args.prompt_file.read_text(encoding="utf-8")
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "host": platform.node(), "platform": platform.platform(), "python": sys.version,
        "base_url": base, "model": model, "gpu_before": gpu_snapshot(),
        "params": {"temperature": 0, "max_tokens": args.max_tokens, "repeat": args.repeat},
        "cases": {},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name, prompt in cases.items():
        report["cases"][name] = []
        for rep in range(args.repeat + 1):
            row = run_case(base, model, prompt, args.max_tokens, args.timeout)
            row["warmup"] = rep == 0
            report["cases"][name].append(row)
            print(json.dumps({"case": name, "rep": rep, "warmup": rep == 0,
                              "wall_s": row["wall_seconds"], "ttft_s": row["first_token_seconds"],
                              "tokens_per_wall_s": row["completion_tokens_per_wall_second"]}), flush=True)
            report["gpu_after"] = gpu_snapshot()
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
