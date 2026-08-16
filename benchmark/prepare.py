from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import tarfile
from pathlib import Path

from .config import ROOT, RUNS, TASKS

FLOOR = Path("/home/cdc/Storage/projects/the-floor")
DAILY = Path("/home/cdc/Storage/projects/_prototype-bay/daily-ops")
HISTORICAL_COMMIT = "87a75208dd46796fde2b3b687403fdb802e6934e"
DAILY_COMMIT = "e273a8aa66667eb5af6370512fb07a6d76ed2f58"


def packet_text(task_id: str) -> str:
    return (TASKS / task_id / "PACKET.md").read_text(encoding="utf-8")


def packet_hash(task_id: str) -> str:
    return hashlib.sha256(packet_text(task_id).encode()).hexdigest()


def prepare_worktree(run_id: str, task_id: str) -> Path:
    target = RUNS / run_id / "worktree"
    if target.exists():
        raise FileExistsError(f"run worktree already exists: {target}")
    target.mkdir(parents=True)
    if task_id == "historical":
        _extract_git(FLOOR, HISTORICAL_COMMIT, target)
    elif task_id == "daily_ops":
        _extract_git(DAILY, DAILY_COMMIT, target)
    elif task_id == "research":
        shutil.copytree(ROOT / "starters" / "research", target, dirs_exist_ok=True)
    else:
        raise ValueError(task_id)
    subprocess.run(["git", "init", "-b", "benchmark"], cwd=target, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Benchmark", "-c", "user.email=benchmark@invalid", "commit", "-m", "benchmark snapshot"],
        cwd=target, check=True, stdout=subprocess.DEVNULL,
    )
    return target


def _extract_git(repo: Path, commit: str, target: Path) -> None:
    archive = subprocess.check_output(["git", "archive", "--format=tar", commit], cwd=repo)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        # git archive contains only repository-relative regular paths.
        tar.extractall(target, filter="data")
