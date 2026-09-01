"""Run approved operational-v1 models sequentially on a GMKtec llama-server host."""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .run import ROOT, TASKS

LLAMA_SERVER = "/home/cdc/src/llama.cpp/build/bin/llama-server"
PORT = 8081
MODELS = (
    {"model": "translategemma:12b", "slug": "translategemma-12b", "digest": "c2f9a9ca1ec7149f2422581c89937ab0363d9399d9355514d753ee012e99c252", "quantization": "Q4_K_M", "template": "ollama-gemma-turn-template", "blob": "1b2b95e2f0eb9a98a839249ed41dfca71b300f9c389e14581210649fada910ed"},
    {"model": "gpt-oss:120b", "slug": "gpt-oss-120b", "digest": "a951a23b46a1f6093dafee2ea481d634b4e31ac720a8a16f3f91e04f5a40ecd9", "quantization": "MXFP4", "template": "embedded-gguf-jinja", "blob": "6be6d66a3f546d8c19b130dc41dc24b2fc159f84ffbc76a0ee0676205083cf5a"},
)


def now() -> str: return datetime.now(timezone.utc).isoformat()


def server_pids() -> list[int]:
    result = subprocess.run(["pgrep", "-f", f"^{LLAMA_SERVER} --model "], text=True, capture_output=True)
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def stop_server() -> None:
    for pid in server_pids():
        subprocess.run(["kill", str(pid)], check=False)
    deadline = time.monotonic() + 30
    while server_pids() and time.monotonic() < deadline: time.sleep(0.5)


def healthy() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3) as response:
            return response.status == 200
    except OSError: return False


def write_serving_failure(spec: dict, log: Path, reason: str) -> None:
    path = ROOT / "data" / "private" / "results" / "operational_v1" / spec["slug"] / f"serving-failure-{datetime.now().strftime('%H%M%S')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"stage": "operational_v1", "at": now(), "model": spec, "status": "serving_failure", "reason": reason, "server_log": str(log)}, indent=2) + "\n", encoding="utf-8")


def start(spec: dict) -> tuple[Path, int] | None:
    stop_server(); log = Path(f"/tmp/operational-v1-{spec['slug']}-server.log")
    handle = log.open("w", encoding="utf-8")
    process = subprocess.Popen([LLAMA_SERVER, "--model", f"/usr/share/ollama/.ollama/models/blobs/sha256-{spec['blob']}", "--host", "127.0.0.1", "--port", str(PORT), "--ctx-size", "16384", "--n-predict", "4096", "--n-gpu-layers", "all", "--flash-attn", "auto", "--jinja", "--metrics", "--no-webui", "--cors-origins", "localhost", "--no-cors-credentials"], stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(90):
        if healthy(): return log, process.pid
        if not server_pids(): break
        time.sleep(1)
    handle.close(); write_serving_failure(spec, log, "llama-server did not become healthy"); return None


def run(spec: dict) -> None:
    started = start(spec)
    if not started: return
    log, server_pid = started
    for task in TASKS:
        command = [sys.executable, "-m", "benchmark.operational_v1.run", "--model", spec["model"], "--slug", spec["slug"], "--digest", spec["digest"], "--quantization", spec["quantization"], "--template", spec["template"], "--task", task, "--endpoint", f"http://127.0.0.1:{PORT}/v1", "--backend", "llama-server", "--backend-version", "b10454-4df29be4f", "--context", "16384", "--timeout", "900", "--server-pid", str(server_pid)]
        completed = subprocess.run(command, cwd=ROOT, env={"PYTHONPATH": str(ROOT)}, text=True, capture_output=True)
        print(completed.stdout, flush=True)
        if completed.returncode: write_serving_failure(spec, log, f"runner exit {completed.returncode}"); break
    stop_server()


if __name__ == "__main__":
    for model in MODELS: run(model)
