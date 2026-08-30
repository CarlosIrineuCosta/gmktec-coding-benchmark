"""Disposable loopback-server lifecycle support used by future candidate runs."""
from __future__ import annotations

import socket
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


def reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_health(url: str, timeout_seconds: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 300:
                    return True
        except OSError:
            pass
        time.sleep(0.25)
    return False


@dataclass
class DisposableServer:
    command: Sequence[str]
    health_url: str
    cwd: Path
    process: subprocess.Popen[str] | None = None

    def start(self, timeout_seconds: float = 30.0) -> int:
        if self.process is not None:
            raise RuntimeError("server already started")
        self.process = subprocess.Popen(
            list(self.command), cwd=self.cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if not wait_for_health(self.health_url, timeout_seconds):
            self.stop()
            raise TimeoutError(f"server did not become healthy: {self.health_url}")
        return self.process.pid

    def stop(self, timeout_seconds: float = 10.0) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout_seconds)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout_seconds)

    def __enter__(self) -> "DisposableServer":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()
