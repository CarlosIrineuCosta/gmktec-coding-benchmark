#!/usr/bin/env python3
"""Persistent, non-mutating five-minute monitor for the Victorian matrix."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(os.environ["VICTORIAN_MATRIX_ROOT"])
INTERVAL = 300


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def command(*args: str) -> dict[str, object]:
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    return {"returncode": result.returncode, "stdout": result.stdout[-8000:], "stderr": result.stderr[-2000:]}


def health() -> dict[str, object]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:18889/api/health", timeout=10) as response:
            return {"ok": response.status == 200, "status": response.status, "body": response.read(4000).decode("utf-8", "replace")}
    except Exception as exc:  # no Studio is expected during download-only phase
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def snapshot() -> dict[str, object]:
    status_path = ROOT / "status.json"
    try:
        status = json.loads(status_path.read_text())
    except Exception as exc:
        status = {"read_error": f"{type(exc).__name__}: {exc}"}
    disk = shutil.disk_usage(ROOT)
    return {
        "observed_at": utc_now(),
        "status": status,
        "disk": {"total": disk.total, "used": disk.used, "free": disk.free},
        "matching_processes": command("pgrep", "-af", str(ROOT)),
        "tmux": command("tmux", "list-sessions"),
        "studio_health": health(),
        "completion_marker": (ROOT / "matrix-complete").exists(),
    }


def main() -> None:
    ROOT.joinpath("logs").mkdir(parents=True, exist_ok=True)
    stream = ROOT / "logs" / "monitor.jsonl"
    latest = ROOT / "monitor.json"
    while True:
        item = snapshot()
        latest.write_text(json.dumps(item, indent=2) + "\n")
        with stream.open("a") as log:
            log.write(json.dumps(item, separators=(",", ":")) + "\n")
        if item["completion_marker"]:
            return
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
