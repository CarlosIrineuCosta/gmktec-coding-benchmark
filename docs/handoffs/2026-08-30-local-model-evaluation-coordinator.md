# Coordinator handoff — 2026-08-30 local-model evaluation

## /goal

Prepare the new `cdc`/Unsloth Studio GMKtec evaluation project so that, once the owner supplies the exact two-model pilot selection, Codex can run the pilot under active supervision and preserve valid autonomous/recovery evidence without reviving the retired August 16 infrastructure.

## Authoritative source for this campaign

Read first:

1. `docs/intake/gpt/2026-08-30/local-model-evaluation-spec.md`
2. `docs/architecture/2026-08-30-supervised-unsloth-evaluation.md`
3. this handoff

The root `README.md` and `docs/next_steps.md` describe the retired August 16 campaign and **must not govern the new execution** where they conflict with the dated 2026-08-30 material.

## Current owner intent

- The benchmark should model real work, not standard leaderboard performance.
- Three task families are planned: greenfield gallery generation, code review, and EN -> PT-BR literary translation.
- Start with a **two-model pilot**.
- Do not infer the pilot pair from what is installed/downloading. Charles will name the exact models separately.
- If the pilot works, expand the same suite without rerunning the pilot pair merely because more candidates are added.
- Context stress testing is not the purpose; use a generous safe ceiling and realistic task context.
- Recoverability under normal human-like feedback is part of the evaluation, but autonomous performance must remain separately scored.

## Critical supervision rule

**A monitor process is not the supervisor. Codex is the supervisor.**

For actual model execution:

- establish `/goal` for the long-running evaluation;
- Codex stays in the control loop;
- helper processes may collect telemetry, but do not satisfy supervision by themselves;
- at approximately five-minute checkpoints, Codex actively inspects run/server/file/test/tool state, reasons about progress, records a supervisory decision, and continues;
- process launch, server health, monitor launch, or partial output are never task completion.

Use the I0/I1/I2/I3/I4 intervention classes defined in the architecture/source spec. I4 is forbidden as benchmark assistance.

## Live GMKtec boundary already established by owner audit

The new campaign is under `cdc`.

Previously verified during the live audit:

- persistent Unsloth Studio user service on `0.0.0.0:18888`;
- Studio authentication enabled;
- Studio uses `/home/cdc/Models/Unsloth/huggingface` as its HF root;
- bundled llama.cpp exposes `Vulkan0: Radeon 8060S Graphics (RADV STRIX_HALO)`;
- `/srv/llm-runner` is deleted;
- `llm-runner` user/group are deleted;
- `/home/cdc/llm` old vLLM cache/environment is deleted;
- obsolete vLLM Docker/ROCm images are deleted;
- historical evidence remains under `/home/cdc/old-tests/gmktec-local-model-eval-2026-08`;
- Ollama may remain enabled but is not a primary lane;
- current Unsloth/HF model store is the canonical active model-byte location.

At handoff time, Unsloth Studio was already downloading Qwen3.8-Flash-Next. Do not interrupt or rearrange in-progress HF downloads.

Before pilot execution, capture a fresh machine/runtime/model manifest rather than assuming the audit values are still exact.

## Setup work to perform now

Do **not** start real candidate inference during setup.

Prepare:

1. machine/runtime/model inventory capture;
2. exact artifact identity recording (repo + revision + filename + bytes + hash where practical);
3. one primary local OpenAI-compatible tool harness with full trajectory logging;
4. isolated disposable model-server lifecycle support;
5. autonomous vs supervised-recovery run-state model;
6. intervention logging;
7. stall/loop detection;
8. failure isolation so one run cannot abort later unrelated runs;
9. gallery fixture and observable Playwright acceptance tests;
10. private held-out code-review fixture/gold data under `data/private/`;
11. translation-input contract awaiting the owner's text;
12. run evidence schemas and compact report generation;
13. mock/fake-model tests for the orchestration and supervision machinery;
14. pilot configuration that remains intentionally incomplete until the owner names the exact two models.

## Repository placement rules

Follow the owner-defined surfaces:

- raw GPT source: `docs/intake/gpt/2026-08-30/`
- canonical prompts/task packets: `tasks/<suite-name>/`
- accepted methodology/harness decisions: `docs/architecture/2026-08-30-<topic>.md`
- formal ADRs, if needed: `docs/adr/ADR-<nnn>-<topic>.md`
- coordinator handoffs: `docs/handoffs/`
- results/analysis: `docs/reports/`
- sanitized public artifacts: `community/artifacts/<suite-name>/`
- raw outputs, hidden gold, local run state, credentials, unredacted transcripts: `data/private/` only

Do not commit model weights, HF caches, secrets, large raw logs, virtual environments, node_modules, or operational authentication material.

## Public repository boundary

The repository is intentionally public so GPT/ChatGPT and other collaborators can reliably access the tracked coordination surface.

This does not change the secrecy boundary: tracked Git content must remain sanitizable and non-secret. Raw outputs, hidden gold data, local run state, credentials, unredacted transcripts, authentication material, and anything potentially secret remain under the gitignored `data/private/` boundary or another explicitly local-only surface. Existing Floor/Codex safety rules against exposing secrets continue to apply.

## Stop condition for setup

Setup is ready when the harness/fixtures/evidence pipeline are validated with mocks/dummy processes, the fresh machine/model manifest can be captured, and the only remaining execution inputs are owner decisions such as the exact pilot models and translation source.

Then report readiness. **Do not choose or launch pilot models without the owner's explicit model-selection instruction.**