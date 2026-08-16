from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .config import HIDDEN, RESULTS, RUNS


def _timing_contaminated(run_id: str) -> bool:
    path = RESULTS / "timing-contamination.json"
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return any(row.get("run_id") == run_id for row in data.get("events", []))


def _pytest(repo: Path, test_targets: list[Path | str] | None = None):
    command = ["python3", "-m", "pytest", "-q"]
    if test_targets:
        command.extend(str(target) for target in test_targets)
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True, timeout=900, env={"PATH": __import__('os').environ.get("PATH", ""), "PYTHONPATH": str(repo / "src")})
    text = result.stdout + result.stderr
    passed = sum(int(value) for value in re.findall(r"(\d+) passed", text))
    failed = sum(int(value) for value in re.findall(r"(\d+) failed", text))
    errors = sum(int(value) for value in re.findall(r"(\d+) error", text))
    total = passed + failed + errors
    return {"exit_code": result.returncode, "passed": passed, "failed": failed, "errors": errors, "total": total, "output": text[-20000:]}


def _ratio(result):
    return result["passed"] / result["total"] if result["total"] else (1.0 if result["exit_code"] == 0 else 0.0)


def score_run(result_file: Path):
    record = json.loads(result_file.read_text())
    worktree = RUNS / record["run_id"] / "worktree"
    task = record["task"]
    baseline = _pytest(worktree)
    with tempfile.TemporaryDirectory(prefix="coding-benchmark-score-") as temp:
        repo = Path(temp) / "repo"; shutil.copytree(worktree, repo, ignore=shutil.ignore_patterns(".git"))
        acceptance = HIDDEN / task / "acceptance"
        acceptance_targets: list[Path] = []
        if acceptance.exists():
            shutil.copytree(acceptance, repo, dirs_exist_ok=True)
            node_manifest = HIDDEN / task / "acceptance_nodes.txt"
            if node_manifest.exists():
                acceptance_targets = [
                    str(repo / node.split("::", 1)[0]) + "::" + node.split("::", 1)[1]
                    for node in node_manifest.read_text(encoding="utf-8").splitlines()
                    if node.strip()
                ]
            else:
                acceptance_targets = [
                    repo / path.relative_to(acceptance)
                    for path in sorted(acceptance.rglob("test*.py"))
                ]
        functional = _pytest(repo, acceptance_targets)
    diff = subprocess.run(["git", "diff", "--numstat"], cwd=worktree, text=True, capture_output=True).stdout
    changed = 0
    for line in diff.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit(): changed += int(parts[0]) + int(parts[1])
    security_ratio = _ratio(functional)  # security boundary tests are included in each hidden set
    scope_ratio = max(0.0, 1.0 - max(0, changed - 1200) / 4800)
    timing_contaminated = _timing_contaminated(record["run_id"])
    efficiency_ratio = 0.0 if record["status"] != "completed" else max(0.0, 1.0 - record.get("wall_seconds", 1800) / 3600)
    components = {
        "functional_45": round(45 * _ratio(functional), 3),
        "regression_15": round(15 * _ratio(baseline), 3),
        "security_10": round(10 * security_ratio, 3),
        "scope_10": round(10 * scope_ratio, 3),
        "blind_review_10": None,
        "efficiency_10": None if timing_contaminated else round(10 * efficiency_ratio, 3),
    }
    return {
        "run_id": record["run_id"], "task": task, "system_id": record["system_id"],
        "automated_score_out_of_90": round(sum(value for value in components.values() if value is not None), 3),
        "components": components, "baseline": baseline, "functional": functional,
        "changed_lines": changed, "manual_review_pending": True,
        "timing_contaminated": timing_contaminated,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=("historical", "research", "daily_ops"))
    args = parser.parse_args()
    paths = sorted(RESULTS.glob("*__ctx*.json"))
    if args.task:
        paths = [path for path in paths if json.loads(path.read_text(encoding="utf-8"))["task"] == args.task]
    with ThreadPoolExecutor(max_workers=3) as executor:
        rescored = list(executor.map(score_run, paths))
    output = RESULTS / "scores.json"
    scores = rescored
    if args.task and output.exists():
        merged = {row["run_id"]: row for row in json.loads(output.read_text(encoding="utf-8"))}
        merged.update({row["run_id"]: row for row in rescored})
        scores = [merged[key] for key in sorted(merged)]
    output.write_text(json.dumps(scores, indent=2) + "\n")
    print(json.dumps([{k: row[k] for k in ("run_id", "automated_score_out_of_90")} for row in scores], indent=2))


if __name__ == "__main__": main()
