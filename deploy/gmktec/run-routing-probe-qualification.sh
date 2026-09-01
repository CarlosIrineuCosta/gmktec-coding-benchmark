#!/usr/bin/env bash
# Run one disposable, telemetry-backed qualification routing probe.
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
port=${ROUTING_PROBE_PORT:?set a unique loopback port}
model=${QUALIFICATION_MODEL_PATH:?set the exact GGUF path}
slug=${QUALIFICATION_SLUG:?set a stable model slug}
model_id=${QUALIFICATION_MODEL_ID:?set the model identifier}
revision=${QUALIFICATION_REVISION:?set the artifact snapshot revision}
quantization=${QUALIFICATION_QUANTIZATION:?set the selected quantization}
model_sha256=${QUALIFICATION_MODEL_SHA256:?set the local artifact SHA-256}
context=${QUALIFICATION_CONTEXT:-16384}
reasoning=${QUALIFICATION_REASONING:-auto}
reasoning_effort=${QUALIFICATION_REASONING_EFFORT:-default}
reasoning_preserve=${QUALIFICATION_REASONING_PRESERVE:-0}
llama_server=${LLAMA_SERVER:-/home/cdc/.unsloth/llama.cpp/build/bin/llama-server}
backend_version=${BACKEND_VERSION:-0.3.0-dev-build10687-92b19177a}
run_root="$repo_root/data/private/results/routing_probe/$slug"
run_stamp=$(date -u +%Y%m%dT%H%M%SZ)
lifecycle_telemetry="$run_root/server-lifecycle-$run_stamp.json"
server_log="$run_root/server-$run_stamp.log"
stop_file="$run_root/stop-telemetry-$run_stamp"

mkdir -p "$run_root"
if ss -ltn | grep -q ":$port "; then
  echo "refusing to reuse occupied port $port" >&2
  exit 2
fi
if [[ ! -x "$llama_server" || ! -f "$model" ]]; then
  echo "required server executable or model artifact is unavailable" >&2
  exit 2
fi

reasoning_args=(--reasoning "$reasoning" --reasoning-effort "$reasoning_effort")
probe_reasoning_args=(--reasoning "$reasoning" --reasoning-effort "$reasoning_effort")
if [[ "$reasoning_preserve" == 1 ]]; then
  reasoning_args+=(--reasoning-preserve)
  probe_reasoning_args+=(--reasoning-preserve)
fi

server_pid=
telemetry_pid=
cleanup() {
  touch "$stop_file"
  if [[ -n "$telemetry_pid" ]]; then wait "$telemetry_pid" || true; fi
  if [[ -n "$server_pid" ]] && kill -0 "$server_pid" 2>/dev/null; then
    kill "$server_pid" || true
    wait "$server_pid" || true
  fi
}
trap cleanup EXIT INT TERM

"$llama_server" \
  --model "$model" \
  --host 127.0.0.1 \
  --port "$port" \
  --ctx-size "$context" \
  --gpu-layers 999 \
  --flash-attn on \
  --jinja \
  "${reasoning_args[@]}" \
  --metrics \
  --no-webui >"$server_log" 2>&1 &
server_pid=$!

PYTHONPATH="$repo_root" python3 -m benchmark.operational_v1.telemetry \
  --server-pid "$server_pid" \
  --output "$lifecycle_telemetry" \
  --stop-file "$stop_file" &
telemetry_pid=$!

for _ in $(seq 1 900); do
  if curl -fsS --max-time 3 "http://127.0.0.1:$port/health" >/dev/null; then break; fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    echo "llama-server exited before health; inspect $server_log" >&2
    exit 3
  fi
  sleep 1
done
if ! curl -fsS --max-time 3 "http://127.0.0.1:$port/health" >/dev/null; then
  echo "llama-server did not become healthy within 15 minutes" >&2
  exit 4
fi

PYTHONPATH="$repo_root" python3 -m benchmark.operational_v1.routing_probe \
  --model "$model_id" \
  --slug "$slug" \
  --revision "$revision" \
  --quantization "$quantization" \
  --model-sha256 "$model_sha256" \
  --endpoint "http://127.0.0.1:$port/v1" \
  --backend-version "$backend_version" \
  --context "$context" \
  "${probe_reasoning_args[@]}" \
  --timeout 1200 \
  --server-pid "$server_pid" \
  --server-lifecycle-telemetry "$lifecycle_telemetry"
