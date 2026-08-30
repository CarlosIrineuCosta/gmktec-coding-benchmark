"""Read-only host/model inventory capture for the new Unsloth campaign."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _command(argv: list[str]) -> dict[str, Any]:
    executable = shutil.which(argv[0])
    if executable is None:
        return {"available": False, "argv": argv}
    completed = subprocess.run(argv, text=True, capture_output=True, timeout=15, check=False)
    return {
        "available": True,
        "argv": argv,
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-4000:],
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_artifact(path: Path, hash_file: bool = False) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    record: dict[str, Any] = {
        "path": str(path),
        "resolved_path": str(resolved),
        "filename": resolved.name,
        "bytes": resolved.stat().st_size,
    }
    if hash_file:
        record["sha256"] = sha256(resolved)
    return record


def capture(model_paths: list[Path], hash_files: bool = False) -> dict[str, Any]:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "uid": os.getuid(),
        },
        "runtime": {
            "unsloth_version": _command(["unsloth", "--version"]),
            "vulkan": _command(["vulkaninfo", "--summary"]),
            "memory": _command(["free", "-b"]),
        },
        "models": [model_artifact(path, hash_files) for path in model_paths],
        "notes": [
            "Capture is read-only and does not load a model.",
            "Repository/revision must be supplied from the managed Hugging Face snapshot metadata.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a read-only local-model runtime manifest")
    parser.add_argument("--model", action="append", default=[], type=Path, help="exact GGUF path; repeatable")
    parser.add_argument("--hash-models", action="store_true", help="calculate SHA-256 (slow for large GGUFs)")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = capture(args.model, args.hash_models)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
