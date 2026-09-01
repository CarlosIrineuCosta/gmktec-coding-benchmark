"""Non-invasive per-run host telemetry for local model evaluation.

The collector reads procfs and AMDGPU sysfs only.  It never changes a driver,
server, GPU setting, or service.  A missing GPU counter is evidence about the
host capability, not a zero-usage measurement.
"""
from __future__ import annotations

import glob
import json
import os
import argparse
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, value = line.split(":", 1)
            fields = value.split()
            if fields and fields[0].isdigit():
                values[key] = int(fields[0])
    except OSError:
        return {}
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if total is not None and available is not None:
        values["MemUsed"] = total - available
    return values


def _rss_kib(pid: int | None) -> int | None:
    if pid is None:
        return None
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except (OSError, ValueError):
        return None
    return None


def _read_counter(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _drm_totals(entries: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    """Sum DRM accounting once per client, not once per duplicated file descriptor."""
    unique: dict[tuple[str | None, str], dict[str, Any]] = {}
    for entry in entries:
        client = entry.get("client_id") or f"fd:{entry.get('fd')}"
        unique.setdefault((entry.get("driver"), str(client)), entry)
    vram = [entry.get("vram_bytes") for entry in unique.values() if isinstance(entry.get("vram_bytes"), int)]
    gtt = [entry.get("gtt_bytes") for entry in unique.values() if isinstance(entry.get("gtt_bytes"), int)]
    return (sum(vram) if vram else None, sum(gtt) if gtt else None)


def _drm_process_memory(pid: int | None) -> dict[str, Any]:
    """Read DRM's per-file-descriptor accounting for a process, if exposed."""
    if pid is None:
        return {"status": "unavailable", "reason": "llama-server PID was not supplied", "entries": []}
    entries: list[dict[str, Any]] = []
    try:
        paths = list(Path(f"/proc/{pid}/fdinfo").iterdir())
    except OSError:
        return {"status": "unavailable", "reason": "llama-server fdinfo was not readable", "entries": []}
    for path in paths:
        values: dict[str, str] = {}
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith(("drm-driver:", "drm-client-id:", "drm-memory-vram:", "drm-memory-gtt:")):
                    key, value = line.split(":", 1)
                    values[key] = value.strip()
        except OSError:
            continue
        if not values.get("drm-driver"):
            continue
        def counter(key: str) -> int | None:
            fields = values.get(key, "").split()
            if not fields or not fields[0].isdigit():
                return None
            value = int(fields[0])
            return value * 1024 if len(fields) > 1 and fields[1].lower() == "kib" else value
        entries.append(
            {
                "fd": path.name,
                "driver": values["drm-driver"],
                "client_id": values.get("drm-client-id"),
                "vram_bytes": counter("drm-memory-vram"),
                "gtt_bytes": counter("drm-memory-gtt"),
            }
        )
    vram_bytes, gtt_bytes = _drm_totals(entries)
    return {
        "status": "available" if vram_bytes is not None or gtt_bytes is not None else "unavailable",
        "reason": None if vram_bytes is not None or gtt_bytes is not None else "DRM fdinfo did not expose VRAM/GTT counters for llama-server",
        "vram_bytes": vram_bytes,
        "gtt_bytes": gtt_bytes,
        "entries": entries,
    }


def revalidate_drm_totals(payload: dict[str, Any]) -> dict[str, Any]:
    """Recalculate an older telemetry payload that summed duplicate DRM FDs."""
    corrected = json.loads(json.dumps(payload))
    for sample in corrected.get("samples", []):
        process_memory = sample.get("amd_gpu", {}).get("process_memory", {})
        if process_memory.get("entries"):
            vram_bytes, gtt_bytes = _drm_totals(process_memory["entries"])
            process_memory["vram_bytes"] = vram_bytes
            process_memory["gtt_bytes"] = gtt_bytes
            process_memory["status"] = "available" if vram_bytes is not None or gtt_bytes is not None else "unavailable"
    counter_paths = corrected.get("summary", {}).get("amd_gpu", {}).get("counter_paths", [])
    corrected["summary"] = summarize(corrected.get("samples", []), [])
    corrected["summary"]["amd_gpu"]["counter_paths"] = counter_paths
    corrected["revalidated"] = {
        "reason": "Deduplicated repeated DRM fdinfo entries by driver and client_id.",
        "collector_correction": "per-client DRM memory accounting",
    }
    return corrected


def discover_amdgpu_counters() -> list[dict[str, Path]]:
    """Return readable AMDGPU memory-counter groups without requiring tools."""
    counters: list[dict[str, Path]] = []
    for raw in glob.glob("/sys/class/drm/card*/device/mem_info_vram_used"):
        vram = Path(raw)
        device = vram.parent
        counters.append(
            {
                "card": Path(raw).parents[1],
                "vram_used": vram,
                "vram_total": device / "mem_info_vram_total",
                "gtt_used": device / "mem_info_gtt_used",
            }
        )
    return counters


def summarize(samples: list[dict[str, Any]], gpu_counter_paths: list[dict[str, Path]]) -> dict[str, Any]:
    def peak(field: str) -> int | None:
        values = [sample["system_memory_kib"][field] for sample in samples if field in sample.get("system_memory_kib", {})]
        return max(values) if values else None

    rss_values = [sample.get("llama_server", {}).get("rss_kib") for sample in samples]
    gpu_available = any(sample.get("amd_gpu", {}).get("status") == "available" for sample in samples)
    process_vram = [sample.get("amd_gpu", {}).get("process_memory", {}).get("vram_bytes") for sample in samples]
    process_gtt = [sample.get("amd_gpu", {}).get("process_memory", {}).get("gtt_bytes") for sample in samples]
    return {
        "sample_count": len(samples),
        "system_memory_kib": {
            "minimum_available": min((sample["system_memory_kib"]["MemAvailable"] for sample in samples if "MemAvailable" in sample.get("system_memory_kib", {})), default=None),
            "peak_used": peak("MemUsed"),
        },
        "llama_server": {
            "peak_rss_kib": max((value for value in rss_values if isinstance(value, int)), default=None),
            "pid_observed": any(sample.get("llama_server", {}).get("rss_kib") is not None for sample in samples),
        },
        "amd_gpu": {
            "status": "available" if gpu_available else "unavailable",
            "peak_llama_server_vram_bytes": max((value for value in process_vram if isinstance(value, int)), default=None),
            "peak_llama_server_gtt_bytes": max((value for value in process_gtt if isinstance(value, int)), default=None),
            "counter_paths": [{key: str(value) for key, value in group.items()} for group in gpu_counter_paths],
            "reason": None if gpu_available else "Neither AMDGPU sysfs nor DRM fdinfo exposed VRAM/GTT counters to the benchmark user",
        },
    }


class TelemetrySampler:
    """Collect one run's host metrics in a daemon thread and write JSON evidence."""

    def __init__(self, server_pid: int | None, interval_seconds: float = 1.0):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.server_pid = server_pid
        self.interval_seconds = interval_seconds
        self.gpu_counter_paths = discover_amdgpu_counters()
        self.samples: list[dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="operational-v1-telemetry")

    def sample_once(self) -> None:
        memory = _meminfo()
        gpu_devices: list[dict[str, Any]] = []
        for counters in self.gpu_counter_paths:
            values = {
                "card": str(counters["card"]),
                "vram_used_bytes": _read_counter(counters["vram_used"]),
                "vram_total_bytes": _read_counter(counters["vram_total"]),
                "gtt_used_bytes": _read_counter(counters["gtt_used"]),
            }
            gpu_devices.append(values)
        process_memory = _drm_process_memory(self.server_pid)
        self.samples.append(
            {
                "at": utcnow(),
                "monotonic_seconds": round(time.monotonic(), 6),
                "system_memory_kib": {key: memory[key] for key in ("MemTotal", "MemAvailable", "MemUsed") if key in memory},
                "llama_server": {"pid": self.server_pid, "rss_kib": _rss_kib(self.server_pid)},
                "amd_gpu": {
                    "status": "available" if process_memory["status"] == "available" or any(device["vram_used_bytes"] is not None or device["gtt_used_bytes"] is not None for device in gpu_devices) else "unavailable",
                    "process_memory": process_memory,
                    "devices": gpu_devices,
                },
            }
        )

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self.sample_once()

    def start(self) -> None:
        self.sample_once()
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        self._thread.join(timeout=self.interval_seconds + 2)
        self.sample_once()
        return summarize(self.samples, self.gpu_counter_paths)

    def write(self, path: Path, summary: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "collector": "benchmark.operational_v1.telemetry",
                    "collection_started_at": self.samples[0]["at"] if self.samples else None,
                    "collection_finished_at": self.samples[-1]["at"] if self.samples else None,
                    "interval_seconds": self.interval_seconds,
                    "summary": summary,
                    "samples": self.samples,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def main() -> None:
    """Run a server-lifecycle collector from a disposable launcher script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-pid", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--revalidate-input", type=Path)
    parser.add_argument("--revalidate-output", type=Path)
    args = parser.parse_args()
    if args.revalidate_input or args.revalidate_output:
        if not args.revalidate_input or not args.revalidate_output:
            parser.error("--revalidate-input and --revalidate-output must be used together")
        args.revalidate_output.write_text(json.dumps(revalidate_drm_totals(json.loads(args.revalidate_input.read_text(encoding="utf-8"))), indent=2) + "\n", encoding="utf-8")
        return
    if args.server_pid is None or args.output is None or args.stop_file is None:
        parser.error("--server-pid, --output, and --stop-file are required for lifecycle collection")
    sampler = TelemetrySampler(args.server_pid, args.interval)
    sampler.start()
    try:
        while Path(f"/proc/{args.server_pid}").exists() and not args.stop_file.exists():
            time.sleep(0.2)
    finally:
        sampler.write(args.output, sampler.stop())


if __name__ == "__main__":
    main()
