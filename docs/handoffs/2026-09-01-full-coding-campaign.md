# Full local coding campaign — 2026-09-01

## /goal

Execute the full GMKtec local coding campaign across the nine already-qualified candidate configurations and carry every scheduled cell to durable terminal evidence. This is an execution authorization, not a request for another benchmark design, readiness memo, or qualification discussion.

The campaign must produce real model work. Do not stop after preflight, dependency repair, model inventory, canaries, the first candidate, the first task, or an individual failure. Continue sequentially until every scheduled model/task cell below has a valid terminal classification and the consolidated public report has been committed and pushed.

Use active Codex supervision throughout. A helper process may collect telemetry, but Codex remains the supervisor. Use `/goal` for continuity. Read compact run state and recent evidence at checkpoints; do not repeatedly reread complete trajectories unless a diagnosis requires it.

---

## 1. Authority and precedence

Execute on:

`agent/local-model-evaluation-pilot-20260830`

Authoritative prior evidence:

- `docs/reports/2026-09-01-c-benchmark-qualification.md`
- `docs/reports/2026-08-30-two-model-pilot.md`
- `docs/architecture/2026-08-30-supervised-unsloth-evaluation.md`
- `docs/architecture/2026-08-30-evaluation-setup-contract.md`

The qualification report establishes that all nine configurations can serve and perform a bounded tool action when their qualified model-specific tool representations are used. The tiny deterministic patch result is qualification metadata only. A candidate that did not pass that exact-format task is NOT excluded from this campaign and must not be described as generally failed.

Do not resurrect the retired August-16 `llm-runner` flow or its terminal 30-minute policy.

---

## 2. Mandatory Phase 0 — dependency closure BEFORE model execution

Before loading the first candidate, inspect the complete declared campaign for ordinary prerequisites and close them in one pass.

Verify at minimum:

- benchmark branch/HEAD and clean enough worktree state;
- Python/project environment and test runner;
- `git`, `curl`, `jq` or equivalent utilities actually used by the runner;
- Node/npm/npx versions used by the gallery fixture;
- Playwright package and Chromium browser;
- Chromium host libraries by actually launching a minimal headless Chromium smoke page at BOTH target viewports;
- gallery private image corpus exists and matches its manifest/hashes;
- code-review private fixture and gold scorer exist and are readable by the scorer but inaccessible to candidates;
- current `llama-server` executable/version and Vulkan device;
- DRM telemetry source used by the qualification runner;
- writable `data/private/` evidence root;
- enough free disk and no incomplete model download locks for the selected artifacts;
- no conflicting disposable benchmark server or model process is resident;
- selected loopback ports are free;
- all nine exact qualified model artifacts are present;
- all required native/adapted tool-call representations from the qualification pass are available;
- final report/output paths are writable.

### Repair-and-continue authority

Ordinary missing prerequisites are **repair-and-continue conditions**, not campaign blockers.

You are explicitly authorized to install or repair ordinary dependencies required by the declared benchmark, including project-local packages and ordinary Ubuntu packages required by Node/Playwright/Chromium/test execution. Verify each repair and continue.

Do NOT stop merely because a package, browser library, npm dependency, Python package, local fixture, or ordinary CLI is missing.

Escalation/stop boundaries remain: kernel, firmware/BIOS, Mesa/RADV or GPU driver replacement, boot configuration, partitions/storage layout, Tailscale/network exposure changes, secrets/credentials, destructive ambiguity involving unrelated data, or unrelated production/project changes.

Do not alter persistent Unsloth Studio authentication or expose disposable servers beyond loopback.

When Phase 0 is complete, record one compact preflight event and immediately begin model execution. **Do not return to the owner with a readiness report.**

---

## 3. Candidate matrix — run ALL nine

Use the exact qualified artifacts/configurations already recorded by the qualification run. Do not substitute variants without recording an I0 artifact/configuration failure and continuing to the next candidate.

1. `unsloth/Qwen3.8-27B-GGUF` — `UD-Q6_K_XL` — coding reference/control
2. `unsloth/Qwen3.8-Flash-Next-GGUF` — `UD-Q3_K_XL`
3. `unsloth/Qwen3.5-9B-GGUF` — `UD-Q6_K_XL`
4. `unsloth/NVIDIA-Nemotron-3-Nano-4B-GGUF` — `UD-Q8_K_XL`
5. `unsloth/gemma-4-31B-it-GGUF` — `UD-Q6_K_XL`
6. `unsloth/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF` — `UD-Q8_K_XL`
7. `unsloth/Llama-3_3-Nemotron-Super-49B-v1-GGUF` — `UD-Q6_K_XL`
8. `unsloth/Llama-3_3-Nemotron-Super-49B-v1_5-GGUF` — `UD-Q6_K_XL`
9. `mradermacher/ASearcher-Web-QwQ-i1-GGUF` — `i1-Q5_K_M`

ASearcher receives no network-search advantage in this campaign; it is evaluated as the locally installed configuration.

The Nano 4B result is especially relevant to a potential fast/housekeeping role; do not judge it solely against heavy-model expectations.

---

## 4. Efficient execution order

Run one model server at a time.

For each candidate:

1. start the exact qualified disposable loopback server/tool representation;
2. verify health and a tiny bounded tool canary;
3. start a **fresh isolated code-review session/workspace** and run Task R;
4. archive/terminalize Task R;
5. start a **fresh isolated gallery session/workspace** and run Task G while the same model remains resident;
6. archive/terminalize Task G;
7. stop the disposable model server and verify it is gone;
8. proceed immediately to the next model.

Do not reuse conversation state between review and gallery.

Suggested model order is the numbered order above. The review-first order intentionally yields a cheap substantive result for each model before the longer gallery run.

A failure in one task does not cancel the other task for that model. A failure in one model does not stop later models.

---

## 5. Task R — held-out code review

Use the existing canonical code-review packet and private held-out fixture/gold scorer from the supervised-evaluation project.

The candidate is a REVIEWER, not an implementer.

Candidate contract:

- inspect the supplied fixture using the qualified tool interface;
- report at most 8 findings;
- each finding must identify location, severity, defect, consequence, recommended correction, and confidence;
- do not reward style/lint speculation as substantive defects;
- do not expose the private gold data.

### Review supervision rule

The scored review is autonomous with respect to substance.

Allowed during the review lane:

- I0 infrastructure repair;
- interface/configuration correction that restores the exact already-qualified tool representation without revealing fixture answers.

Do not give I1/I2/I3 hints about defects, locations, missing findings, or correctness. If the model cannot complete the review without substantive help, classify the autonomous review accordingly rather than coaching it.

### Review scoring

Record at least:

- credited gold defects;
- gold defect total;
- recall;
- reported finding count;
- credited finding count;
- non-gold/false-positive finding count;
- finding-level precision;
- hallucinated/nonexistent paths;
- required-field compliance;
- useful severity/location quality where the scorer can assess it;
- wall time;
- TTFT;
- tool calls;
- malformed/repeated calls;
- prompt/output token accounting where available;
- peak system RSS plus DRM VRAM/GTT telemetry as separate measurements;
- terminal classification.

Keep the corrected arithmetic invariant: `reported = credited + non-gold` at finding level. The previously preserved Qwen review correction was 5 / 3 / 2 / recall 1.00 / precision 0.60.

---

## 6. Task G — one-shot greenfield photo gallery

This is the primary real coding-generation task.

Use the existing fixed 12-image local public-domain corpus and canonical gallery packet/starter. Every model gets the same local assets and the same observable requirements.

“One-shot” means the model receives one complete initial product brief and begins from the same starter. It may inspect files, write code, run tests/builds, and iterate using tools. Codex does not pre-solve the task.

The product must be a polished responsive local photo gallery, approximately requiring:

- all 12 supplied images represented without broken assets;
- responsive gallery/grid handling mixed aspect ratios;
- usable desktop and mobile layouts;
- lightbox/modal viewing;
- next/previous controls;
- keyboard left/right navigation;
- Escape closes the lightbox;
- captions/metadata visible meaningfully;
- focus/keyboard behavior that remains usable;
- reasonable image loading behavior;
- no material console/page errors;
- production build succeeds;
- TypeScript/typecheck succeeds where defined by the starter.

Do not prescribe a particular component architecture or CSS strategy.

### Browser acceptance

The browser environment has now been remediated. Before the campaign begins, Phase 0 must prove Chromium can launch.

For every gallery artifact run the same Playwright/observable acceptance at at least:

- desktop: 1440x900;
- mobile: 390x844.

Capture standardized screenshots at both viewports plus a representative open-lightbox state. Store raw screenshots under private evidence. A compact sanitized contact sheet or selected screenshots may be published under `community/artifacts/` only if they reveal no private/local information.

Explicitly test the defect discovered in the preserved Qwen artifact: the lightbox close control must remain visible and operable at 390x844.

### Gallery scoring

Do NOT turn the gallery into one binary pass/fail number.

Record independently:

- build success;
- typecheck success;
- Playwright assertions passed/total;
- desktop functional acceptance;
- mobile functional acceptance;
- lightbox controls;
- keyboard navigation;
- close-control visibility/operation on mobile;
- console/page errors;
- image completeness;
- standardized screenshot paths/hashes;
- autonomous completion yes/no;
- final completion after allowed supervision yes/no;
- interventions by class;
- wall time;
- time to first meaningful edit if available;
- time to first successful build if available;
- tool calls and repeated/malformed calls;
- prompt/output token accounting where available;
- peak system RSS plus DRM VRAM/GTT telemetry as separate measurements;
- terminal classification.

Human visual/aesthetic judgment is deliberately deferred. Preserve the screenshots/artifact so Charles can inspect them later without model identity bias if desired.

---

## 7. Autonomous vs supervised gallery behavior

Stage A begins with the complete one-shot packet and no substantive Codex help.

Codex actively supervises but should let useful work proceed.

If the candidate stalls, loops, falsely declares completion, or has actionable failures, Stage B may use the existing intervention classes:

- I0 infrastructure: repair/restore infrastructure;
- I1 diagnostic: provide raw/minimally interpreted test/build/runtime result;
- I2 criterion reminder: identify an unmet acceptance criterion without implementation direction;
- I3 directional hint: bounded direction toward a subsystem/conceptual issue;
- I4 substantive implementation by Codex: forbidden as benchmark assistance.

Always preserve the autonomous result separately from the final supervised result.

A useful artifact that needs I1–I3 recovery is still useful evidence; do not flatten it to generic `fail`.

---

## 8. Progress, checkpoints, loops, and termination

Codex remains actively responsible for the campaign.

At approximately five-minute intervals during long active runs, inspect a COMPACT state view containing only what is needed to decide:

- process/server alive;
- latest model turn/tool action;
- worktree/file change summary;
- latest build/test status;
- loop signature/repeated actions;
- elapsed time since meaningful progress;
- current intervention state;
- telemetry summary/deltas where useful.

Do not reread the complete transcript or entire repository at every checkpoint. Raw evidence remains durable and can be opened only when diagnosis requires it. This is intended to reduce the extreme Codex supervisory token overhead observed in qualification while preserving active supervision.

Two consecutive checkpoints without meaningful progress trigger a supervisory decision, not an automatic kill.

Meaningful progress includes coherent source changes, a new useful diagnostic, improving tests, investigation of a new failure, or a genuinely active long model generation.

There is no universal 30-minute terminal timeout.

Terminate a cell when:

- acceptance work is complete and the model has finished;
- the model is genuinely unrecoverable under allowed supervision;
- destructive behavior occurs;
- a persistent no-progress loop survives reasonable intervention;
- required infrastructure cannot be restored without crossing the explicit escalation boundary.

Classify the reason precisely. Prefer terms such as `accepted`, `accepted_with_defects`, `supervised_completion`, `task_not_completed`, `server_compatibility_blocked`, or `infrastructure_blocked` over a generic `fail`.

If the campaign runs beyond the owner's approximate eight-hour unattended window but active candidates are still making meaningful progress, continue. Machine time itself is not a cost boundary.

---

## 9. Model-native runtime settings

Reuse the exact serving/tool representations that passed the 2026-09-01 qualification gate, including the documented Nemotron representations/adapters.

Do not force every family through a universal tool template.

For task sampling/reasoning, prefer the already-qualified/documented family configuration. Keep the TASK identical but treat model-native chat template, reasoning mode, adapter, and sampling as part of the tested configuration.

Record every effective setting in each run manifest.

Do not silently change a candidate's configuration mid-task. An I0 correction to restore a documented/qualified configuration must be recorded; then restart that cell cleanly if the earlier attempt was invalidated.

Use a realistic generous context ceiling supported by the model/runtime; do not pad context. The 16K qualification setting does not constrain the real gallery/review campaign. 64K is an acceptable default where already proven safe, with lower/larger effective context recorded if required by a specific model configuration.

---

## 10. Evidence and artifact boundary

Public GitHub may contain:

- this handoff;
- runner/harness code;
- canonical public task packets;
- sanitized model/runtime identities;
- compact metrics;
- scoring summaries;
- sanitized screenshots/artifacts intended for comparison;
- final analysis/report.

Keep under `data/private/` or other already-gitignored local evidence:

- raw model trajectories/reasoning;
- complete tool transcripts;
- private code-review gold fixture/scoring map;
- raw local process/environment paths when not appropriate for publication;
- authentication material/tokens;
- huge logs;
- unsanitized screenshots/output containing local/private information.

No credentials are required for this campaign beyond already-working Git publication. Do not seek Google Drive or unrelated connected data.

---

## 11. Required consolidated outputs

When all 18 scored cells (9 models × 2 tasks) are terminal, produce and PUSH:

`docs/reports/2026-09-01-full-local-coding-campaign.md`

Also produce a compact machine-readable sanitized summary, preferably:

`community/artifacts/local-model-evaluation/2026-09-01-summary.json`

The report must contain:

### A. Campaign validity

- exact branch/HEAD;
- runtime/server version;
- Phase-0 dependency closure result;
- statement that each candidate used its qualified tool representation;
- deviations/restarts/invalidated attempts;
- proof disposable servers were stopped at end.

### B. Per-model profile

For every model, show code-review and gallery outcomes side by side, plus telemetry and intervention counts. Do not produce only one overall leaderboard score.

### C. Role-oriented synthesis

Identify evidence-supported candidates for roles such as:

- tiny/fast housekeeping;
- routine local coding;
- heavy/difficult coding;
- code review;
- strongest autonomous gallery generation;
- strongest recoverable gallery generation;
- unacceptable operational/tool behavior, if any.

The Qwen 3.8 27B Q6 deterministic qualification pass is useful evidence but is not automatically the campaign winner. The rich tasks decide the routing recommendation.

### D. Gallery artifact index

Provide paths/hashes for the standardized screenshots and final workspaces so Charles can inspect what was actually built.

### E. Defect language

Avoid generic `fail` when the result is narrower. State exactly what happened: malformed output contract, missed behavior, hallucinated finding, mobile defect, tool incompatibility, infrastructure issue, incomplete task, etc.

---

## 12. Campaign completion condition

This instruction is complete only when:

1. Phase 0 dependency closure was performed and ordinary prerequisites repaired;
2. all nine exact candidates were attempted;
3. each candidate received both Task R and Task G in fresh sessions/workspaces;
4. all 18 scored cells have terminal evidence;
5. all disposable model servers/listeners are gone;
6. raw private evidence is preserved locally;
7. the consolidated report and sanitized summary are committed and pushed;
8. the final response reports the branch/HEAD and concise result table.

Do not stop to request approval between candidates or ordinary repairs. Do not stop after a canary. Do not stop after producing a readiness summary. Do not stop because one model/task fails. Do not stop because the protected `main` branch is untouched; this campaign is authorized on the existing agent branch.

If one explicit escalation boundary is reached, preserve that cell as blocked and continue every independent cell that does not require crossing that boundary.
