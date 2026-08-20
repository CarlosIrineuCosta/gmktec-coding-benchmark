#!/usr/bin/env python3
"""Fetch and checksum the exact GGUF roster for the Victorian search matrix."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


ROOT = Path(os.environ["VICTORIAN_MATRIX_ROOT"])
HF_HOME = Path(os.environ["HF_HOME"])
MODELS = (
    ("Q35-9", "unsloth/Qwen3.5-9B-GGUF", "Qwen3.5-9B-UD-Q6_K_XL.gguf"),
    ("Q38-UD", "unsloth/Qwen3.8-27B-GGUF", "Qwen3.8-27B-UD-Q6_K_XL.gguf"),
    ("Q38-Q6", "unsloth/Qwen3.8-27B-GGUF", "Qwen3.8-27B-Q6_K.gguf"),
    ("GLM", "unsloth/GLM-4.7-Flash-GGUF", "GLM-4.7-Flash-UD-Q6_K_XL.gguf"),
    ("GEMMA", "unsloth/gemma-4-26B-A4B-it-GGUF", "gemma-4-26B-A4B-it-UD-Q6_K_XL.gguf"),
)


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_status(**payload: object) -> None:
    (ROOT / "status.json").write_text(
        json.dumps({"updated_at": now(), **payload}, indent=2) + "\n"
    )


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    HF_HOME.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    api = HfApi()
    for key, repository, filename in MODELS:
        write_status(phase="download", current_model=key, completed=[m["id"] for m in manifest])
        info = api.model_info(repository, files_metadata=True)
        remote = next((s for s in info.siblings if s.rfilename == filename), None)
        if remote is None:
            raise RuntimeError(f"{repository} does not publish {filename} at {info.sha}")
        target_dir = ROOT / "models" / key
        target_dir.mkdir(parents=True, exist_ok=True)
        failure: Exception | None = None
        for attempt, delay in enumerate((0, 20, 60), start=1):
            if delay:
                time.sleep(delay)
            try:
                local = Path(
                    hf_hub_download(
                        repo_id=repository,
                        filename=filename,
                        revision=info.sha,
                        cache_dir=str(HF_HOME),
                        local_dir=str(target_dir),
                    )
                )
                failure = None
                break
            except Exception as exc:  # network failures are retried and recorded
                failure = exc
                write_status(
                    phase="download_retry",
                    current_model=key,
                    attempt=attempt,
                    error=f"{type(exc).__name__}: {exc}",
                )
        if failure is not None:
            raise failure
        actual_sha = sha256(local)
        manifest.append(
            {
                "id": key,
                "repository": repository,
                "filename": filename,
                "revision": info.sha,
                "bytes": local.stat().st_size,
                "sha256": actual_sha,
                "hf_lfs_sha256": getattr(getattr(remote, "lfs", None), "sha256", None),
                "local_path": str(local),
                "verified_at": now(),
            }
        )
        (ROOT / "download-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    write_status(phase="download_complete", current_model=None, completed=[m["id"] for m in manifest])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
