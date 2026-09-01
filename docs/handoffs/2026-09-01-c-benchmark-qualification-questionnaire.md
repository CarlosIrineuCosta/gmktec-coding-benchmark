# c-benchmark qualification execution questionnaire — 2026-09-01

## /goal

Produce the concrete evidence needed for GPT to issue the final larger-model campaign task file. **Run code and tests now. Do not return another methodology proposal.** Stop only when the requested evidence below exists in durable local/private state and the sanitized summary is committed/pushed.

This is authorization for the bounded qualification work below. It is not authorization for the full model campaign yet.

## 1. Publish the runner state you already proved

The public branch currently visible to GPT ends at the Aug-30 pilot. If the newer runner/telemetry/small-task-gate implementation exists only locally/private:

- commit and push all **sanitized code, schemas, task definitions, and methodology/report changes** needed to reproduce it;
- keep raw outputs, secrets, hidden fixtures, unredacted transcripts, and private run state under `data/private/` or local-only;
- report the exact branch + HEAD.

Do not wait for a PR/main merge.

## 2. Fix the known benchmark-host defect

Install the ordinary Playwright/Chromium host libraries needed for the existing gallery acceptance test. This is authorized host-test remediation; do not alter kernel, Mesa/RADV, firmware, storage, Tailscale, or unrelated services.

Then run the browser acceptance stack on a deterministic local fixture and prove Chromium launches successfully.

Record PASS/FAIL and the exact remediation performed.

## 3. Reconcile the Qwen review score

The Aug-30 report states: 5 findings, 3 credited, precision 0.60, and 3 non-gold findings. Those counts are internally inconsistent under ordinary finding-level precision.

Run the scorer against the preserved private Qwen review evidence and report the exact:

- total findings;
- credited findings;
- false/non-gold findings;
- recall;
- precision;
- scoring unit/rule.

Correct the public report if needed. Do **not** rerun Qwen review unless the scorer/evidence itself is invalid.

## 4. Inventory the currently installed public local models

You are authorized to inventory the canonical Unsloth/HF model store and propose role labels. Do not download extra models merely to fill categories.

For each installed candidate record:

- repository;
- revision/snapshot;
- exact GGUF filename/shards;
- quant;
- bytes;
- hash where practical;
- apparent intended role: `tiny_fast`, `medium_general`, `heavy_reasoning_coding`, `specialized`, or `unknown`.

Installed does not mean selected.

## 5. Run a serving/tool qualification gate on every plausible coding/agent candidate

For each plausible coding/agent candidate already installed, run:

### Gate A — serving canary

- disposable loopback server;
- exact artifact identity;
- server health;
- one short deterministic generation;
- capture model load time, TTFT if available, decode tokens/s, RSS/RAM, and Vulkan/GTT/VRAM-equivalent telemetry available on this platform;
- clean teardown.

### Gate B — tool/interface canary

Determine the **documented/native tool-call interface for that model** rather than forcing one universal template.

- If native OpenAI-style tool calls are documented/supported, qualify that path.
- If the model documents another structured tool format, a clearly labelled compatibility adapter may be used for qualification.
- Record `reasoning on/off`, chat template, adapter/template choice, and exact result.
- One successful bounded read/action is enough to pass the tool canary.
- A failed canary is `configuration/tool_compatibility_blocked`, not a model-quality failure.

For Nemotron Super specifically, explicitly test the NVIDIA-documented tool-call format / appropriate reasoning mode before declaring it incompatible.

## 6. Run the same small deterministic qualification task for models that pass the canaries

Use the runner's already-proven small deterministic task.

Rules:

- same task and observable acceptance criteria for every candidate;
- model-native reasoning/template/sampling settings may differ and must be recorded;
- no universal hard wall-clock kill timer; use existing progress/stall policy;
- no substantive Codex implementation assistance;
- preserve telemetry and terminal classification;
- failure of one candidate must not stop later candidates.

This is a **qualification gate**, not the final campaign ranking.

## 7. Supervisor efficiency

Active Codex supervision remains required, but do not repeatedly reread full trajectories. Use compact durable checkpoint state/summaries and inspect raw trajectory only when needed.

Record approximate Codex supervisory token usage for this qualification pass if available.

## 8. Deliverable — answer these questions with evidence

Create a concise report under `docs/reports/` and answer:

1. What branch/HEAD now contains the sanitized current runner/gate implementation?
2. Does Playwright/Chromium acceptance now run successfully on GMKtec?
3. What is the corrected Qwen review score/count?
4. Which exact models are currently installed and plausible for coding/agent work?
5. For each candidate: serving canary PASS/FAIL, tool canary PASS/FAIL, deterministic qualification task PASS/FAIL.
6. What documented template/adapter/reasoning mode was required for each candidate?
7. What throughput/load/memory telemetry was observed?
8. Which candidates should advance to the representative-task campaign, grouped by role?
9. What concrete blocker, if any, remains before GPT can write the final campaign task MD?

Do not respond with a request for another methodology brief. **Run the above qualification work and return the evidence.**
