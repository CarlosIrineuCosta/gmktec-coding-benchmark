# Qwen routing probe with host telemetry — 2026-09-01

## Decision

`Qwen3.8-Flash-Next` UD-Q3_K_XL is eligible for **supervised, deterministic-
validated, small offline patch suggestions** on GMKtec. This is one positive
synthetic no-tool result, not a qualification for safe-unattended work,
agent/tool operation, internal-project edits, or multi-file repository tasks.

The earlier Qwen image-gallery one-shot remains separate qualitative evidence.
Historical benchmark reports and artifacts were not rerun, rewritten, or
overwritten.

## Exact run

- Model repository/revision: `unsloth/Qwen3.8-Flash-Next-GGUF` at
  `c8b5954a88c2775c546b92593eda40ea041d3176`.
- Quant: `UD-Q3_K_XL`; three SHA-256-verified shards:
  `f2ef4328929d8b8c8930e2856eef52128dd4ce3425302f04bc3c657431cc4c49`,
  `7d230e7c9421d868b89eebaf23033af0ea1a4e046956df00fb156814fb62346e`, and
  `21d4f90f9cd7b7c3a1582667c20cb22f7b03de895b88a23bb20aaeaa44f2c199`.
- Server: local Unsloth `llama-server` `0.3.0-dev`, build `10687`, commit
  `92b19177a`; loopback-only port `18903`.
- Server parameters: 64K context, all layers requested on GPU, Flash Attention
  on, Jinja template, reasoning on, `xhigh` reasoning effort, and reasoning
  preservation.
- Request: temperature `1.0`, top-p `0.95`, top-k `20`, min-p `0`, maximum
  output `4096`; no tools, network, or private source material.
- Task: new public synthetic `retry.py` patch; return one unified diff. Three
  standard-library `unittest` checks validate normalization and the exclusive
  three-attempt bound.

## Result

The model returned a concise standard unified diff that normalized `status` and
changed the retry bound from `<= 3` to `< 3`.

- Request wall time: `00:00:21.065`.
- First-token latency: `00:00:17.989`.
- Usage reported by the server: 247 prompt tokens, 541 completion tokens.
- Streaming parser: zero malformed events; server stop reason `stop`.
- Acceptance: **passed 3/3** under evaluator correction commit `83f0ffd`.

The first evaluator record is preserved but invalidated as a harness defect: it
required an `a/` filename prefix although the packet allowed the standard
`--- retry.py` form that Qwen returned. The unchanged response, SHA-256
`f2894997889a0d9ae3d10b766332ef6593f0674858f0835683426b2e2b0c6308`, was
re-scored with the corrected evaluator. No second model call occurred.

## Measured resources

One-second lifecycle telemetry ran from model process start through task
completion (43 samples); request telemetry captured 23 samples. Values below
are peaks across both corrected records.

- System RAM used: 92,538,032 KiB (88.25 GiB); minimum available RAM:
  36,924,824 KiB (35.21 GiB).
- `llama-server` RSS: 28,612,320 KiB (27.29 GiB).
- AMD GPU VRAM attributed to the server: 1,830,391,808 bytes (1.70 GiB).
- AMD GTT attributed to the server: 62,971,375,616 bytes (58.65 GiB).

The collector reads procfs, AMDGPU sysfs, and DRM `fdinfo`; it changes no
driver, package, service, network, or GPU setting. A follow-up collector
correction (`bf2b58b`) deduplicated two DRM file descriptors that referred to
the same client ID. The original raw telemetry remains present; separate
`*-revalidated-bf2b58b.json` files provide the corrected values above.

## Evidence and non-actions

Private raw evidence remains under the disposable GMKtec root
`/home/cdc/.local/share/gmktec-benchmark-pilot/private/routing-probe-runtime/repo/data/private/results/routing_probe/`:
the prompt, raw answer, original run record, request/lifecycle telemetry, and
both correction records. It is Git-ignored and was not published.

The first launch attempt failed before the script began because its log target
directory did not yet exist. No model process started and no token was
generated; the second attempt was the allowed infrastructure-before-first-token
retry. The disposable server stopped after the run; port `18903` has no
listener. Persistent Unsloth Studio was not restarted or reconfigured.

## Source and next routing rule

The public harness and probe are committed locally in `d72462b`, `862644c`,
`83f0ffd`, and `bf2b58b`. They are not pushed or merged.

Route this exact Qwen configuration only to small, synthetic/public or
otherwise independently authorized offline patch tasks with deterministic
application and test validation plus human review. Do not infer autonomous
agent, tool-use, production, private-code, or broad coding suitability from
this one task. A future expansion requires a new Owner instruction.
