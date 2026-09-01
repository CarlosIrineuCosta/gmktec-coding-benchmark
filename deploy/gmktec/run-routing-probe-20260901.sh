#!/usr/bin/env bash
# Run exactly one disposable, telemetry-backed synthetic routing probe.
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
port=${ROUTING_PROBE_PORT:-18903}
llama_server=/home/cdc/.unsloth/llama.cpp/build/bin/llama-server
model=/home/cdc/Models/Unsloth/huggingface/hub/models--unsloth--Qwen3.8-Flash-Next-GGUF/snapshots/c8b5954a88c2775c546b92593eda40ea041d3176/UD-Q3_K_XL/Qwen3.8-Flash-Next-UD-Q3_K_XL-00001-of-00003.gguf
run_root="$repo_root/data/private/results/routing_probe/qwen38-flash-next-ud-q3-k-xl"
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
  echo "required server executable or model shard is unavailable" >&2
  exit 2
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
  --ctx-size 65536 \
  --gpu-layers 999 \
  --flash-attn on \
  --jinja \
  --reasoning on \
  --reasoning-effort xhigh \
  --reasoning-preserve \
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
  --model local \
  --slug qwen38-flash-next-ud-q3-k-xl \
  --revision c8b5954a88c2775c546b92593eda40ea041d3176 \
  --quantization UD-Q3_K_XL \
  --model-sha256 7d230e7c9421d868b89eebaf23033af0ea1a4e046956df00fb156814fb62346e \
  --endpoint "http://127.0.0.1:$port/v1" \
  --backend-version "0.3.0-dev-build10687-92b19177a" \
  --context 65536 \
  --timeout 1200 \
  --server-pid "$server_pid" \
  --server-lifecycle-telemetry "$lifecycle_telemetry"
