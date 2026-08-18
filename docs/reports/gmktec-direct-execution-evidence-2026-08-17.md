# GMKtec Direct Execution Evidence — 2026-08-17

This records the direct, isolated execution authorized by Charles while the
existing Floor coordinator is internally blocked. No Floor queue, Dev request,
or production runtime was used.

## Scope and isolation

- TesseraFold work ran in the disposable worktree
  `/tmp/tesserafold-gmktec-search-repair-20260817` on branch
  `codex/gmktec-search-repair-20260817`.
- The canonical TesseraFold checkout was already dirty and was not modified.
- Model outputs and disposable environments are under `/tmp`; no secret values
  are recorded here.

## Issue 1 — local application/coding test

### Defect shaped and fixed

`ScopedPostgresStore.search` creates `search_vector` from `title`, `summary`,
`body_markdown`, and `source_body_markdown`, but its pg_trgm fallback only
searched title, summary, and source body. A misspelled query whose only relevant
occurrence was in the curated `body_markdown` could therefore fail candidate
selection despite the exact term being in the full-text index.

Commit `941ebe2` (`fix: include card body in v2 trigram search`) adds
`body_markdown` to both the trigram score and the fallback predicate. A
regression test captures the generated SQL and parameter order, asserting both
body fields have parity.

### Verification

- `python -m pytest tests/test_store_v2.py -q` from `apps/api` using a
  disposable dependency environment: **10 passed**.
- `py_compile` passed for both modified Python files.
- The broader API test module cannot collect at the checked-out base revision:
  `ModuleNotFoundError: No module named 'app.output'`. This existed outside the
  two-file change and was not repaired or masked.
- Direct local review used `qwen3-coder:30b` at `http://gmktec:11434/api/chat`
  with temperature zero, 73 evaluated tokens, and a 5.10-second total duration.
  Its verdict was `CORRECT`; it identified no concrete SQL or ranking issue.

## Issue 2 — independent architecture task comparison

All runners received the same neutral source packet at
`/tmp/gmktec-architecture-source-packet.md`; no successful runner received a
peer answer.

| Requested model | Result | Evidence |
|---|---|---|
| Terra High (`gpt-5.6-terra`) | Completed | Read-only, ephemeral run created a concrete Floor Redux architecture: admission ledger, local controller, isolated workspace runner, model router, broker/evidence store; typed direct-recovery lifecycle and three acceptance tests. Output: `/tmp/gmktec-architecture-terra-output.txt`. |
| Kimi K3 (`kimi-code/k3-256k`) | Runner did not produce a final answer | The configured profile was verified to select K3. Its safe noninteractive invocation entered plan mode and ended without a final response. A retry requiring `-y` was rejected because it would let the runner self-approve tool calls. No bypass was used. |
| GLM-5.3 | Unavailable through configured Claude runner | A no-tools, no-session invocation reported that `glm-5.3` was not recognized or accessible. Output: `/tmp/gmktec-architecture-glm-5.3-output.txt`. |

The comparison is therefore **not complete**: one independent substantive answer
exists, and two failures are captured rather than represented as model output.

## Issue 3 — Strands direct proof

The disposable proof at `/tmp/floor-strands-poc-2026-08-17` was rerun against
the live GMKtec OpenAI-compatible endpoint. It uses `strands-agents 1.52.0`,
role/capability metadata, and `qwen3.6:35b-a3b`.

Observed sequence:

1. Role requires a local, tool-capable route.
2. Metadata late-binds `gmktec-openai-compatible` at
   `http://gmktec:11434/v1`.
3. The `route_evidence` tool is called once.
4. The returned result is `gmktec-openai-compatible`.
5. The route and result are captured in the external disposable evidence file
   `/tmp/floor-strands-poc-2026-08-17/evidence.json`.

The model did not receive durable coordinator state; evidence is stored outside
its context in the disposable run artifacts.
