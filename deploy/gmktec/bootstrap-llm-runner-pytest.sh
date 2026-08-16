#!/usr/bin/env bash
# Run as llm-runner on GMKtec.  Creates only the runner-owned benchmark venv.
set -euo pipefail

readonly RUNNER_HOME=/srv/llm-runner
readonly VENV="$RUNNER_HOME/venv"
readonly PYTEST_VERSION=9.1.1

if [[ $(id -un) != llm-runner ]]; then
  echo "run as llm-runner" >&2
  exit 2
fi

python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install "pytest==$PYTEST_VERSION"
"$VENV/bin/python" -m pytest --version
