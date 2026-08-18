# GMKtec Execution Outcome — External Supervisor Handoff

Date: 2026-08-17

Purpose: evidence-grounded current state for an external GPT supervisor. This is
not authority to mutate Floor, reconfigure production services, or infer that
an unstarted GitHub work order was executed.

## Executive state

The GMKtec local-inference lab completed its approved disposable tests. The host
is `gmktec`; use dynamic MagicDNS and never encode historical `gmtek` or a
fixed address. The stable Ollama daemon remained untouched.

GitHub issues #1, #2, and #3 were delivered to and consumed by `floor-dev`, but
each ADR-028 admission stopped before claim/start because authoritative
`floor-dev` tmux-generation evidence is missing. No TesseraFold worktree or
patch, GLM/Kimi/Terra comparison, or Floor-authorized Strands worker ran.

One separate disposable Strands proof ran outside production Floor: role
metadata selected GMKtec's OpenAI-compatible route, invoked one tool, and
returned `gmktec-openai-compatible`. It supports only the narrow adapter
hypothesis; it does not replace the blocked Issue #3 work order.

## Confirmed GMKtec lab outcomes

### Isolated Ollama context contract

An isolated secondary daemon on loopback port 11435 served deterministic
Qwen3-Coder 30B Q4 probes at 8K, 16K, 32K, and 64K. `/api/ps` observed each
selected allocation. Request-level `options.num_ctx` overrode the fresh daemon
default in both tested directions: 8K server plus 16K request produced 16K;
64K server plus 8K request produced 8K.

The temporary Modelfile experiment was safely blocked because Ollama `create`
attempted metadata changes on a production blob supplied read-only. The
temporary store was removed. This is not a model failure or context result.

### Serving qualification

- Qwen3-Coder with llama-server/Vulkan at 8K completed the controlled
  sequential-tool canary. A later missing-`pytest` failure is an executor
  environment defect, not a model/tool failure.
- Qwen3-Coder Next and GPT-OSS passed a minimal native-Ollama sequential-tool
  loop at 8K.
- TranslateGemma 12B passed basic native Ollama serving at 8K; translation
  quality remains unqualified.
- GLM-4.6V-Flash has a package-default 4K `num_ctx`, not a 4K-native model
  limit; a fresh explicit 8K request observed 8K.

### vLLM/ROCm

Docker Engine 29.7.2 was installed on GMKtec. An isolated loopback-only
`vllm/vllm-openai-rocm@sha256:bb44b39...bd80f0e7` container passed model-list,
completion, and chat tests with a ROCm/Triton fallback on the Radeon 8060S.
Containers were removed after capture.

The pinned BF16 checkpoint
`Qwen/Qwen3-Coder-30B-A3B-Instruct@b2cff646eb4bb1d68355c01b18ae02e7cf42d120`
loaded and served at 8K. This is a serving-contract pass, not a direct
comparison with the 18.56 GB Q4 GGUF baseline.

At 1/2/4/8 concurrent requests, the small Qwen smoke recorded 94.01 / 202.91 /
394.23 / 444.18 aggregate completion tokens/s, zero errors, and 29–95 ms TTFT.
On fixed coding and extraction workloads, vLLM had lower four-client TTFT;
the one-client Q4/Vulkan route had higher aggregate completion tokens/s.
Because the artifacts differ (BF16 vs Q4), this is not a pure backend winner.

## Provisional workload routing

- One active coding/tool agent: Qwen3-Coder Q4 via llama-server/Vulkan,
  medium-high confidence.
- Four concurrent coding or prompt-heavy tasks: pinned Qwen3-Coder BF16 via
  disposable vLLM/ROCm, medium confidence.
- Casual/private local chat: existing Ollama/Vulkan route, medium confidence.
- Translation: TranslateGemma on Ollama passes serving only; quality remains
  unqualified.
- GLM: use explicit request context until package defaults are deliberately
  represented.

No production auto-router, Floor provider integration, stable-service change,
or model promotion is authorized by these findings.

## GitHub execution-order status

| Issue | Requested work | Durable outcome |
| --- | --- | --- |
| #1 | TesseraFold search repair and tests | blocked before start; no worktree or file changed |
| #2 | GLM-5.3, Kimi K3, Terra High comparison | blocked before start; no provider route launched |
| #3 | Floor-authorized disposable Strands proof | blocked before start; separate manual proof exists |

The common blocker is `owner_admission_floor_dev_generation_evidence_missing`.
Each issue has a caller-directed response: `FLOOR-14877`, `FLOOR-14881`, and
`FLOOR-14885`. Delivery or consumption is not a claim, start, provider run,
patch, or successful test.

## Evidence

- `docs/reports/gmktec-ollama-context-precedence-2026-08-17.md`
- `docs/reports/gmktec-serving-compatibility-and-vllm-preflight-2026-08-17.md`
- `docs/reports/gmktec-local-inference-routing-matrix-2026-08-17.md`
- `docs/reports/gmktec-qwen3-coder-hf-provenance-2026-08-17.md`
- `docs/reports/floor-role-routing-and-tick-review-2026-08-17.md`
- `/tmp/floor-strands-poc-2026-08-17/role_route_poc.py`
- `/tmp/floor-strands-poc-2026-08-17/evidence.json`

## Instructions to the external supervisor

1. Keep lab evidence distinct from the blocked Floor work orders.
2. Keep role requirements separate from routes: roles name tools, context,
   privacy, cost, and latency; routes name model, provider/server/backend,
   context, and concurrency.
3. Do not hard-code `gmtek`, pinned addresses, or model names into roles.
4. Do not propose a new scheduler, queue, ledger, daemon, or Strands
   replacement for Floor's durable lifecycle machinery.
5. Do not mark the issues complete. Restore authoritative `floor-dev`
   tmux-generation evidence, then retry their existing exact source and
   authorization events.
6. Keep stable Ollama untouched; do not conflate it with disposable lab runs.
