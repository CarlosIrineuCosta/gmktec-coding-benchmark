# GPT source specification — GMKtec local-model evaluation

**Date:** 2026-08-30  
**Status:** source/intake, not canonical execution state  
**Owner:** Charles  
**Target host:** `gmktec`  

## /goal

Build a durable, reproducible local-model evaluation project whose purpose is to determine which locally served open models are actually useful for Charles's real workloads. The project must evaluate autonomous capability, recoverability under realistic supervision, operational behavior, and final artifact quality. It must not collapse serving failures, harness failures, or supervision effort into a single model-quality score.

The eventual execution must use an **active Codex supervisory loop**. A spawned Python watcher, shell loop, daemon, tmux process, cron job, or sleeping monitor does not satisfy the supervision requirement. A helper process may collect telemetry, but Codex itself remains responsible for inspecting state, reasoning about progress, intervening when warranted, and carrying every scheduled run to a valid terminal state.

This document records the GPT-originated source specification. Canonical prompts/task packets belong under `tasks/<suite-name>/`; accepted decisions belong under dated architecture documents or ADRs.

---

## 1. Purpose

This is not primarily a conventional benchmark. It is a private deployment evaluation intended to answer:

- Which locally served models complete representative real work?
- Which finish autonomously?
- Which recover well when given normal human-like feedback?
- How much supervisory effort does each model require?
- How long does useful work take?
- Which models are strongest at greenfield code generation, code review, and literary translation?
- Which model/runtime combinations show pathological operational behavior such as loops, duplicate tool calls, malformed tool calls, excessive retries, false completion, or stalled execution?

The project must distinguish:

1. model capability;
2. serving/runtime failure;
3. agent-harness failure;
4. infrastructure failure;
5. supervision/recovery behavior.

Never turn a serving failure into a model-quality score.

---

## 2. Current campaign boundary

The new campaign runs under user `cdc` and Unsloth Studio/llama.cpp. It **does not** revive the retired `/srv/llm-runner` environment.

Known owner-verified facts at the time of this intake:

- Host: `gmktec`
- Ubuntu 24.04.4 LTS
- Ryzen AI MAX+ 395 / Radeon 8060S
- approximately 123 GiB usable RAM
- Mesa/RADV 26.1.7 observed during audit
- Unsloth Studio installed under `cdc`
- persistent Studio user service on port 18888
- Studio authentication enabled and must remain enabled
- Studio binds `0.0.0.0:18888` for Windows/Tailscale access
- configured Hugging Face/Unsloth model root: `/home/cdc/Models/Unsloth/huggingface`
- bundled llama.cpp exposes `Vulkan0: Radeon 8060S Graphics (RADV STRIX_HALO)`
- `/srv/llm-runner` and its Unix user/group have been deleted
- old `/home/cdc/llm` vLLM tree has been deleted
- obsolete vLLM Docker/ROCm image was pruned
- old-test evidence was moved under `/home/cdc/old-tests/gmktec-local-model-eval-2026-08`
- Ollama may remain installed/running but is not the primary backend for this campaign
- active model bytes should be managed by Unsloth/Hugging Face rather than manually rearranging HF cache blobs

These facts must be independently captured by the new project before execution rather than blindly assumed.

---

## 3. Historical lessons that must govern the redesign

### 3.1 Hidden-test design failure

The previous campaign used hidden tests that assumed undisclosed internal Python/package/module names. Legitimate alternative implementations therefore failed test collection. New hidden tests must evaluate externally observable contracts, not secret implementation layouts.

### 3.2 Arbitrary universal timeout

The old 30-minute terminal timeout was not a valid universal capability boundary. Wall-clock duration is a metric. A slow but progressing model should not automatically fail because thirty minutes elapsed.

### 3.3 Serving failure is not model failure

The prior GPT-OSS 120B path failed at large Ollama context but later completed a small tool canary correctly. Serving/runtime/configuration failures must be separately classified.

### 3.4 Pathological tool loops matter

A prior GLM configuration produced the requested code but emitted 167 tool calls, including 164 duplicate test calls. Final success does not erase unsafe or pathological agent behavior.

### 3.5 One failure must not abort the suite

A failed model/run must be classified and preserved. Unrelated later models/tasks continue.

---

## 4. Two-stage evaluation method

### Stage A — autonomous

Each candidate receives the original task packet. Codex supervises but gives no substantive assistance.

Record at least:

- run start/end;
- exact server/model/artifact identity;
- context/reasoning/sampling settings;
- model output and tool trajectory;
- wall time;
- first meaningful edit;
- first build;
- first passing test;
- files and lines changed;
- commands/tools used;
- malformed or repeated calls;
- runtime errors;
- acceptance results;
- whether the model itself declared completion.

This produces the autonomous result.

### Stage B — supervised recovery

If the model stalls, loops, incorrectly declares completion, receives actionable test feedback, asks a legitimate question, or needs realistic human-like steering, Codex may intervene.

Every intervention must be logged as one of:

- **I0 infrastructure** — restore server/socket/process/dependency infrastructure without changing the intellectual task. No model-quality penalty.
- **I1 diagnostic** — provide raw or minimally interpreted compiler/test/runtime feedback. Small intervention cost.
- **I2 criterion reminder** — identify an unmet acceptance requirement without supplying implementation direction. Meaningful intervention cost.
- **I3 directional hint** — point toward the likely subsystem/conceptual error. Significant intervention cost.
- **I4 implementation** — Codex supplies the substantive solution. **Forbidden as benchmark assistance.** If required, classify the candidate as not recoverable under the allowed supervision contract.

Harness repairs authored by Codex are separate from candidate assistance and must be explicitly classified.

---

## 5. Active supervision contract

During real evaluation runs, Codex itself remains in the control loop.

At least every approximately five minutes, or sooner when an event occurs, Codex must actively:

1. inspect run state;
2. inspect model/server state;
3. inspect meaningful file/worktree changes;
4. inspect recent commands/tool calls;
5. inspect build/test state;
6. detect loops/repeated failures;
7. decide whether intervention is warranted;
8. record that decision;
9. continue supervision.

A helper may sleep. Codex may not delegate away the supervisory obligation and then consider the run monitored.

The real execution session should use `/goal` to preserve this responsibility across long runs and context compaction.

Do not treat any of the following as completion:

- process launched;
- monitor launched;
- server healthy;
- model produced some output.

Completion requires a valid terminal classification and preserved evidence.

---

## 6. Stall and termination policy

Two consecutive supervision checkpoints without meaningful progress should trigger a supervision decision, not automatic termination.

Meaningful progress can include source changes, useful diagnostics, test movement, investigation of a new failure, a coherent new implementation attempt, or a long generation that is genuinely still progressing.

Detect loops such as:

- identical command repeated without changed state;
- identical test repeatedly run without edits;
- repeated malformed tool call;
- rereading the same files without action;
- server continually respawning;
- repeated false-success claims while acceptance remains unchanged.

There is no universal 30-minute kill timer.

Stop a run when:

- acceptance is satisfied and the model has completed;
- the model is unrecoverable after reasonable supervised recovery;
- destructive behavior occurs;
- infrastructure cannot be restored without crossing a safety/configuration boundary;
- a genuine infinite/no-progress loop persists despite intervention.

Always record the terminal reason.

---

## 7. Configuration philosophy

The experimental unit is:

`model checkpoint + exact quant + serving stack + native chat template + reasoning mode + tool contract`

Do not force identical internal reasoning settings when that would make a model run unnaturally. Prefer documented/native settings where possible and record them.

Context is not the primary benchmark target. Use a generous ceiling (normally up to 131072 where safely supported) and let the real task consume what it needs. Do not pad context artificially.

If a candidate cannot serve at the declared ceiling because of memory/runtime behavior, classify that separately and choose the largest stable configuration needed for the real task.

Filename alone is insufficient artifact identity. Capture repository, revision/snapshot, filename, byte size, and hash where practical. This matters because quant payloads may change while retaining filenames such as `UD-Q6_K_XL`.

---

## 8. Serving architecture

Keep persistent Studio on port 18888 for management/convenience. Do not casually disturb it.

For benchmark runs, prefer disposable per-model servers through the installed Unsloth/llama.cpp stack:

```text
Codex active supervisor
        |
evaluation harness
        |
disposable Unsloth/llama-server instance
        |
exact GGUF artifact
        |
Vulkan / RADV
        |
Radeon 8060S
```

Each run should:

1. identify exact artifact;
2. choose a non-conflicting loopback port;
3. start a disposable server;
4. capture command/configuration;
5. wait for real health/readiness;
6. resolve served model identity;
7. begin candidate task;
8. supervise actively;
9. capture evidence;
10. terminate the server cleanly;
11. verify process/port are gone.

Ollama is not part of the new primary comparison unless the owner explicitly adds an Ollama lane later.

---

## 9. Primary harness principle

Prepare one primary external agent/tool harness intended to work with most OpenAI-compatible local models.

Prefer native OpenAI-style tool calls supported through the model's template/server.

Keep coding tools small and auditable, approximately:

- read file;
- list/search files;
- write/patch file;
- run bounded command/test;
- inspect git diff/status.

Tool execution must be confined to the candidate's isolated working directory except for explicitly read-only runtime information.

Log every model turn and tool call.

If native tool calls are not usable:

- do not silently invent an unrecorded parser advantage;
- classify the compatibility problem;
- optionally support a clearly labeled compatibility adapter later.

---

## 10. Corpus A — greenfield photo gallery

The one-shot generation task should build a polished responsive photo gallery from a fixed local corpus of approximately 12–16 legally reusable/public-domain/CC0 images.

For each image preserve source page, creator when available, license/status, local filename, SHA256, dimensions/aspect ratio.

Use varied subjects and aspect ratios: portrait, landscape, square, people, architecture, nature, dark scene, bright scene, high-detail image.

Preferred fixture: React + TypeScript + Vite with dependencies fixed in advance.

Required behavior should include approximately:

- responsive gallery;
- mixed aspect ratios handled correctly;
- lightbox;
- previous/next;
- keyboard navigation;
- Escape to close;
- captions/metadata;
- meaningful focus behavior;
- responsive mobile layout;
- no broken images;
- reasonable loading behavior.

Do not require a particular internal architecture.

Use Playwright for observable-behavior acceptance. Capture standardized desktop/mobile screenshots for Charles's visual judgment. Codex aesthetics are not an authoritative hidden score.

---

## 11. Corpus B — code review

Create a private held-out review fixture with a known set of substantive defects spanning categories such as correctness, lifecycle/state, error handling, validation/boundaries, concurrency/idempotency/replay, and subtle edge cases.

Gold information must be inaccessible to the candidate.

The model acts as reviewer, not implementer, and returns at most a bounded number of findings (e.g. eight), each with location, severity, defect, consequence, recommended correction, and confidence.

Measure true-defect recall, precision, false-positive count, severity quality, location quality, and explanatory usefulness.

Do not reward dozens of speculative warnings.

Codex must not substantively assist during this lane.

---

## 12. Corpus C — literary translation

Charles will supply the English source separately.

The intended task is EN -> PT-BR literary translation. The candidate may receive a longer whole work/chapter as context while translating a defined approximately 1,500–2,500-word range.

Primary human-evaluation dimensions:

- semantic fidelity;
- omission/addition;
- voice/register;
- syntactic intelligence;
- lexical choices;
- rhythm;
- idiomatic PT-BR;
- continuity/terminology;
- paragraph/dialogue preservation.

Automated checks may cover names, numbers, headings, paragraph structure, obvious omissions, and formatting. BLEU is not the principal quality measure.

Charles should review translations blind to model identity. Codex must not improve candidate translations before evaluation.

---

## 13. Results model

Do not collapse everything into one leaderboard number.

Each run should preserve a profile including at least:

- autonomous completion yes/no;
- final completion after allowed supervision yes/no;
- interventions by class;
- hard acceptance results;
- false positives where relevant;
- wall time;
- tool calls;
- repeated/loop calls;
- malformed calls;
- files changed;
- regression state;
- runtime errors;
- model/server configuration;
- human-quality fields.

Later synthesize operational roles such as strongest autonomous coder, strongest supervised coder, strongest reviewer, strongest translator, best quality/speed compromise, and unacceptable tool behavior.

Pilot models initially run once. Interesting/finalist models may later receive three independent repetitions to estimate reliability.

---

## 14. Pilot strategy

Run a **two-model pilot first**. Its purpose is to validate the harness, supervision method, evidence capture, and scoring workflow.

If the pilot works, the full suite should extend the same project and **not rerun those two models merely because the suite expands**.

Do not infer the pilot models from installed/downloaded artifacts. The owner will specify the exact pair separately.

Candidate discussion currently includes, but does not yet select:

- Qwen3.8 Flash Next at a Q3 Dynamic quant;
- Nemotron 3 Nano 30B-A3B;
- Nemotron 3.5 Lightning 30B-A3B;
- DiffusionGemma;
- current Qwen3.8-27B Dynamic 3.0 artifacts;
- other current open models to be considered separately.

Installed != selected.

---

## 15. Run evidence

A run directory should preserve approximately:

```text
runs/<run-id>/
    manifest.json
    request.md
    server.json
    events.jsonl
    interventions.jsonl
    metrics.json
    acceptance.json
    summary.md
    git.diff
```

Huge/unredacted/raw outputs belong under `data/private/`, not tracked Git. Tracked reports should contain compact sanitized evidence and references/hashes to raw material where useful.

Never overwrite a completed run.

---

## 16. Machine cleanliness and safety

Do not alter kernel, BIOS/firmware, Mesa/RADV, partitions, Tailscale, Studio authentication, or unrelated repositories as part of ordinary benchmark execution.

Do not resurrect `/srv/llm-runner` or `/home/cdc/llm`.

Do not manually rearrange Hugging Face cache blobs.

Do not create another sprawling global cache/model namespace.

Project dependencies should remain project-local or clearly isolated.

---

## 17. Setup-phase boundary

Before the pilot, the coordinator should prepare methodology, task fixtures, harness, fake/mock validation, model/machine inventory capture, evidence schemas, and run contracts.

**Do not start candidate inference merely to test the setup.** Use fake/mock model responses and dummy processes where possible.

Setup completion means the pilot can begin immediately once Charles supplies the exact model pair and any remaining corpus input.

---

## 18. Precedence warning

The repository contains legacy material from the August 16 campaign, including `docs/next_steps.md` and a root `README.md` that describe the retired `llm-runner`/Ollama-first flow and a terminal 30-minute timeout.

Those files are historical evidence. They do **not** govern the new `cdc`/Unsloth Studio campaign.

Accepted 2026-08-30 architecture/handoff material must explicitly override those execution assumptions.