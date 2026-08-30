# 2026-08-30 — Supervised Unsloth evaluation architecture

**Status:** accepted for the new `cdc`/Unsloth Studio campaign  
**Supersedes for new runs:** retired August 16 `llm-runner`/Ollama-first execution assumptions, including the universal terminal 30-minute timeout  

## Decision

The GMKtec evaluation is a real-work deployment evaluation, not a single-score benchmark.

The primary runtime for the new campaign is the current `cdc` Unsloth/llama.cpp/Vulkan stack. Persistent Unsloth Studio remains available on port 18888 for management/convenience. Actual benchmark runs should use isolated disposable per-model inference servers where practical so server configuration, artifact identity, lifecycle, and failures can be attributed to one candidate run.

The benchmark records two distinct capability layers:

1. **Autonomous result:** candidate receives the original task and Codex gives no substantive help.
2. **Supervised recovery result:** if necessary, Codex may provide bounded human-like intervention, recorded by intervention class.

Final artifact quality and recoverability are both meaningful, but they are never conflated.

## Active Codex supervision

A background monitor is not the supervisor.

During real runs, Codex itself must stay in an active supervisory loop. A helper may gather telemetry or sleep between checkpoints, but approximately every five minutes (or sooner on events) Codex must inspect state, reason about progress, determine whether intervention is needed, record that decision, and continue until each run reaches a valid terminal classification.

Real execution sessions should use `/goal` to preserve this responsibility during long-running work and context compaction.

## Intervention classes

- **I0 — infrastructure:** restore server/process/socket/dependency infrastructure without changing the intellectual task. No model-quality penalty.
- **I1 — diagnostic:** return raw or minimally interpreted compiler/test/runtime evidence. Small intervention cost.
- **I2 — criterion reminder:** identify an unmet acceptance criterion without implementation direction. Meaningful intervention cost.
- **I3 — directional hint:** identify likely subsystem or conceptual direction. Significant intervention cost.
- **I4 — implementation:** Codex supplies substantive solution. Forbidden as benchmark assistance; if required, candidate is not recoverable under the allowed supervision contract.

Harness repairs by Codex are classified separately from candidate assistance.

## Time and termination

Wall time is a metric, not a universal failure boundary. There is no default terminal 30-minute timeout.

Two consecutive checkpoints without meaningful progress trigger a supervisory decision, not automatic termination.

A run terminates on accepted completion, unrecoverable no-progress after reasonable allowed recovery, destructive behavior, an infrastructure failure that cannot be repaired inside the approved boundary, or a persistent loop despite intervention.

Failure of one candidate/run does not abort unrelated later runs.

## Configuration identity

The evaluated unit is:

`checkpoint + exact quant/artifact + server/backend + native chat template + reasoning configuration + tool contract`

Artifact identity must include repository, revision/snapshot, filename, byte size, and hash where practical. Filename alone is not sufficient.

Context length is not the benchmark target. Use a generous safe ceiling where the model/runtime supports it and let the workload consume what it actually needs. Do not pad context to artificial lengths.

## Task families

The initial project prepares three distinct task families:

1. **Greenfield gallery generation** — fixed local photo corpus, observable Playwright behavior checks, standardized desktop/mobile screenshots, and human visual judgment.
2. **Code review** — bounded findings against a private held-out defect set; measure recall, precision, false positives, severity/location/explanation quality.
3. **EN -> PT-BR literary translation** — source supplied separately by the owner; automated structural checks plus blind human literary evaluation.

The pilot will use exactly two owner-selected models. If the pilot validates the harness/supervision workflow, those results remain part of the full suite and are not rerun merely because more candidates are added.

## Storage/runtime boundary

- Current model bytes belong under the Unsloth/Hugging Face managed store.
- Do not manually reorganize HF cache blobs.
- `/srv/llm-runner` is retired and must not be recreated.
- `/home/cdc/llm` is retired and must not be recreated.
- Historical test evidence under `/home/cdc/old-tests/...` is evidence only, not active configuration.
- Ollama may remain installed/running but is not a primary evaluation lane unless explicitly reintroduced by owner decision.
- Raw/unredacted outputs and potentially sensitive local run state belong under the gitignored `data/private/` boundary.

## Legacy precedence

For the new campaign, this dated architecture note and the corresponding 2026-08-30 coordinator handoff take precedence over legacy execution language in `README.md` and `docs/next_steps.md`. Those files remain useful historical records but must not drive new runs.