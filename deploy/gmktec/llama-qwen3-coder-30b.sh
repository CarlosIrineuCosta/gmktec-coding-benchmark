#!/usr/bin/env bash
# Manual, localhost-only llama-server profile for the controlled Qwen A/B canary.
# It reads the existing Ollama-owned GGUF blob and never changes Ollama's store.
set -euo pipefail

readonly LLAMA_SERVER=/home/cdc/src/llama.cpp/build/bin/llama-server
readonly QWEN_GGUF=/usr/share/ollama/.ollama/models/blobs/sha256-1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a

exec "$LLAMA_SERVER" \
  --model "$QWEN_GGUF" \
  --host 127.0.0.1 \
  --port "${LLAMA_PORT:-8081}" \
  --ctx-size "${LLAMA_CTX_SIZE:-8192}" \
  --n-predict "${LLAMA_N_PREDICT:-1024}" \
  --n-gpu-layers all \
  --flash-attn auto \
  --jinja \
  --metrics \
  --no-webui \
  --cors-origins localhost \
  --no-cors-credentials \
  "$@"
