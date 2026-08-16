#!/usr/bin/env bash
# Readiness gate for every local GMKtec coding harness.
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DEFAULT_VENV=/srv/llm-runner/venv
readonly PYTHON_BIN="${BENCHMARK_PYTHON:-$DEFAULT_VENV/bin/python}"
readonly CANARY_DIR="${1:-$SCRIPT_DIR/../../canaries/python-test-readiness}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "MISSING: benchmark interpreter is not executable: $PYTHON_BIN" >&2
  exit 2
fi

"$PYTHON_BIN" -c 'import pytest; print("pytest", pytest.__version__)'
"$PYTHON_BIN" -m py_compile "$CANARY_DIR/smoke_module.py" "$CANARY_DIR/unboundlocal_fixture.py"
"$PYTHON_BIN" -m pytest -q "$CANARY_DIR"
echo "READY: python test environment verified ($PYTHON_BIN)"
