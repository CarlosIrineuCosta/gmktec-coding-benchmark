#!/usr/bin/env bash
# Run once as root on GMKtec. Creates a non-privileged account for local coding
# harnesses; it does not grant container, Docker, Ollama, or sudo access.
set -euo pipefail

readonly RUNNER=llm-runner
readonly RUNNER_HOME=/srv/llm-runner
# This is the public half of the existing automation key. It is deliberately
# embedded because the private key is held by the controller, not GMKtec.
readonly RUNNER_PUBLIC_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC41rTvcCdTR0uIHtx/xkk5hPFnyM48I1ewequGiMvZA cdc@cdc-SD'

if ! id "$RUNNER" >/dev/null 2>&1; then
  useradd --create-home --home-dir "$RUNNER_HOME" --shell /bin/bash --user-group "$RUNNER"
fi

usermod --lock "$RUNNER"
install -d -o "$RUNNER" -g "$RUNNER" -m 0750 "$RUNNER_HOME"
install -d -o "$RUNNER" -g "$RUNNER" -m 0700 "$RUNNER_HOME/.ssh"
install -d -o "$RUNNER" -g "$RUNNER" -m 0700 \
  "$RUNNER_HOME/workspaces" "$RUNNER_HOME/profile" "$RUNNER_HOME/runtime" "$RUNNER_HOME/logs"

touch "$RUNNER_HOME/.ssh/authorized_keys"
chown "$RUNNER:$RUNNER" "$RUNNER_HOME/.ssh/authorized_keys"
chmod 0600 "$RUNNER_HOME/.ssh/authorized_keys"
if ! grep -qxF "$RUNNER_PUBLIC_KEY" "$RUNNER_HOME/.ssh/authorized_keys"; then
  printf '%s\n' "$RUNNER_PUBLIC_KEY" >> "$RUNNER_HOME/.ssh/authorized_keys"
fi

id "$RUNNER"
getent group "$RUNNER"
stat -c '%A %U:%G %n' "$RUNNER_HOME" "$RUNNER_HOME/.ssh" "$RUNNER_HOME/.ssh/authorized_keys"
