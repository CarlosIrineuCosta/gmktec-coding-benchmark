from __future__ import annotations

import io
import shutil
import subprocess
import tarfile
from pathlib import Path

from .config import ROOT
from .prepare import DAILY, DAILY_COMMIT, FLOOR, HISTORICAL_COMMIT

REFERENCE_FLOOR = "a122054aacad90a48d59532a56a0451739e322ad"
RESEARCH = Path("/home/cdc/Storage/projects/research-toolkit")


def _git_files(repo: Path, commit: str, files: list[str], out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for name in files:
        data = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=repo)
        target = out / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)


def main():
    hidden = ROOT / "hidden"
    if hidden.exists(): shutil.rmtree(hidden)
    # Historical public regression suite from the pre-fix snapshot and hidden
    # acceptance tests from the post-fix reference commit.
    baseline_files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", HISTORICAL_COMMIT, "tests"], cwd=FLOOR, text=True).splitlines()
    _git_files(FLOOR, HISTORICAL_COMMIT, baseline_files, hidden / "historical" / "baseline")
    acceptance = [
        "tests/test_floor_delivery_supervisor.py",
        "tests/test_floor_forward_work_order.py",
        "tests/test_floor_tmux_delivery_send.py",
    ]
    _git_files(FLOOR, REFERENCE_FLOOR, acceptance, hidden / "historical" / "acceptance")
    (hidden / "historical" / "acceptance_nodes.txt").write_text(
        "\n".join([
            "tests/test_floor_delivery_supervisor.py::test_exact_claim_start_consumes_only_its_floor_work_order_source",
            "tests/test_floor_delivery_supervisor.py::test_forwarded_empty_source_event_id_is_never_a_transport_receipt",
            "tests/test_floor_delivery_supervisor.py::test_exact_failed_source_never_schedules_a_third_transport_attempt",
            "tests/test_floor_delivery_supervisor.py::test_tmux_evidence_selection_is_timestamp_then_event_id_stable",
            "tests/test_floor_forward_work_order.py::test_forward_delivery_requires_exact_broker_source",
            "tests/test_floor_forward_work_order.py::test_forward_delivery_passes_broker_event_id_to_tmux_sender",
            "tests/test_floor_tmux_delivery_send.py::test_committed_exact_effect_fence_skips_replay",
        ]) + "\n",
        encoding="utf-8",
    )

    daily_baseline = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", DAILY_COMMIT, "tests"], cwd=DAILY, text=True).splitlines()
    _git_files(DAILY, DAILY_COMMIT, daily_baseline, hidden / "daily_ops" / "baseline")
    for source in (DAILY / "tests").glob("test_*.py"):
        if source.name in {"test_trello_live.py", "test_voice_capture.py"}:
            target = hidden / "daily_ops" / "acceptance" / "tests" / source.name
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    # Research tests and blank-install smoke are hidden from candidates.
    target = hidden / "research" / "acceptance" / "tests"; target.mkdir(parents=True, exist_ok=True)
    for source in (RESEARCH / "tests").glob("test_*.py"): shutil.copy2(source, target / source.name)
    print(hidden)


if __name__ == "__main__": main()
