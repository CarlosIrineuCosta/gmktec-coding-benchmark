#!/usr/bin/env bash
# Objective validation: type-check, build, then run both Playwright suites
# against the built bundle served by `vite preview`.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-4173}"
export GALLERY_URL="${GALLERY_URL:-http://127.0.0.1:${PORT}/}"

echo "== typecheck =="
npx --no-install tsc --noEmit

echo "== build =="
npx --no-install vite build

echo "== preview ${GALLERY_URL} =="
npx --no-install vite preview --host 127.0.0.1 --port "${PORT}" --strictPort >/tmp/gallery-preview.log 2>&1 &
PREVIEW_PID=$!
cleanup() { kill "${PREVIEW_PID}" >/dev/null 2>&1 || true; }
trap cleanup EXIT

for _ in $(seq 1 60); do
  if curl -sf "${GALLERY_URL}" >/dev/null 2>&1; then break; fi
  sleep 0.5
done
curl -sf "${GALLERY_URL}" >/dev/null || { echo "preview server never came up"; cat /tmp/gallery-preview.log; exit 1; }

echo "== canonical contract (tests/) =="
npx --no-install playwright test

echo "== candidate verification (validate/) =="
npx --no-install playwright test --config playwright.validate.config.ts

echo "== all suites passed; artifacts =="
ls -l artifacts
