"""Apply an offline patch response only to a fresh disposable public fixture."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from .fixtures import CODE_FILES


def evaluate(answer_path: Path, output: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="operational-v1-patch-") as raw:
        root = Path(raw)
        for name, text in CODE_FILES.items(): (root / name).write_text(text, encoding="utf-8")
        answer = answer_path.read_text(encoding="utf-8").strip()
        if answer.startswith("```diff") and answer.endswith("```"):
            answer = "\n".join(answer.splitlines()[1:-1]).strip()
        answer += "\n"
        patch = subprocess.run(["patch", "-p1", "--batch"], cwd=root, input=answer, text=True, capture_output=True, timeout=30)
        test = subprocess.run(["python3", "-m", "pytest", "-q"], cwd=root, text=True, capture_output=True, timeout=60) if patch.returncode == 0 else None
        result = {"patch_exit_code": patch.returncode, "patch_output": (patch.stdout + patch.stderr)[-4000:], "test_exit_code": test.returncode if test else None, "test_output": (test.stdout + test.stderr)[-4000:] if test else "", "passed": bool(test and test.returncode == 0), "diff_lines": len(answer.splitlines())}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8"); return result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--answer", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(evaluate(args.answer, args.output), indent=2))


if __name__ == "__main__": main()
