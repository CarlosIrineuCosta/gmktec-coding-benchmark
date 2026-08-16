# GMKtec coding-model evaluation: evidence and backend investigation brief

**Prepared:** 2026-08-16

**Audience:** an LLM or engineer independently reviewing the experiment

**Status:** diagnostic handoff, not a final model ranking

## Later controlled Qwen qualification

After this handoff was drafted, Qwen3-Coder 30B was qualified through
loopback-only llama-server at an independently observed 64K context using a
restricted `llm-runner` Unix account. A minimal single-tool harness passed
three fully specified disposable two-file correction canaries, with exact
`READY` preflight responses and four allowed actions per task. A matched Qwen
Code 0.21.12 plan-mode preflight did not honour the no-tool gate: it registered
a broad platform tool surface and continued with file/shell actions after
emitting `READY`. This is a Qwen Code contract block, not a model-quality
failure. See `docs/reports/2026-08-16-minimal-harness-vs-qwen-code.md`.

OpenCode `1.18.18` was then installed only for the restricted `llm-runner`
user. With ordinary workspace read/edit/shell tools but external-directory,
web, subagent, and skill access denied, it completed the same correction in
17.782 seconds. The exact-path permission profile was incompatible with this
local adapter's relative-path representation; the practical profile relies on
the Unix-user boundary for containment. See
`docs/reports/2026-08-16-opencode-qwen3-coder-qualification.md`.

## Executive summary

Nine coding systems were asked to perform three tasks in isolated worktrees at a
nominal 65,536-token context. The intended 32K/64K/96K/128K context ladder was
explicitly deferred. The first pass produced useful implementation artifacts,
but it is not a valid final leaderboard:

1. The hidden tests for Research and Daily Ops assumed undisclosed module names.
   Implementations using otherwise legitimate package layouts failed collection,
   so their functional score of zero cannot be interpreted as zero capability.
2. The Historical hidden tests were meaningful, but all systems failed most of
   the seven exact-source/replay assertions. Codex Terra passed 2/7, Kimi passed
   1/7, and Codex Sol passed 0/7. Sol nevertheless preserved the broader
   regression suite substantially better than Terra.
3. Kimi exhausted its provider quota during the Historical run. Its Research
   and Daily Ops runs then failed immediately with HTTP 403 and did no work.
4. Z.AI GLM-5.3 hit the 30-minute harness limit on Research and Daily Ops. Its
   Historical run stopped because Claude Code's autocompaction repeatedly
   refilled, not because the nominal model context was exhausted in a simple,
   directly comparable way.
5. `gpt-oss:120b` returned Ollama HTTP 500 at the requested 65,536 context for
   all three main tasks, but later completed a fully specified 8,192-context
   coding canary correctly. This implicates configuration/context/resource or
   serving behavior rather than basic inability to use tools.
6. `MedAIBase/GLM-4.6V-Flash:9b` completed the same 8,192-context canary and
   produced the correct code, but emitted 167 tool calls, including 164 duplicate
   `run_test` calls. The harness had asked for at most one call per turn. This is
   unsafe agent-loop behavior even though the final test passed.
7. The Strix Halo community guide used for GMKtec guidance explicitly recommends
   Ollama as the easiest private-chat route and `llama-server` for local API,
   several tools, long-context tests, and server experiments. This is evidence
   that `llama-server` may better match this benchmark. It is not evidence, by
   itself, that Ollama is incapable of tool use or must be abandoned.

The next useful experiment is a small backend A/B canary—not another full
matrix—using the same GGUF/model, prompt, tools, context, generation cap, and
hardware state through Ollama and `llama-server`.

## Reproducible experiment boundary

Systems:

| System ID | Harness/backend | Model identifier |
|---|---|---|
| `gmktec-qwen3-coder-30b` | custom agent loop / Ollama | `qwen3-coder:30b` |
| `gmktec-qwen3-coder-next` | custom agent loop / Ollama | `qwen3-coder-next` |
| `gmktec-gpt-oss-120b` | custom agent loop / Ollama | `gpt-oss:120b` |
| `gmktec-gemma4-26b` | custom agent loop / Ollama | `gemma4:26b-a4b-it-qat` |
| `gmktec-glm-4.6v-flash-9b` | custom agent loop / Ollama | `MedAIBase/GLM-4.6V-Flash:9b` |
| `zai-glm-5.3-claude` | Claude Code 2.1.226 / Z.AI Anthropic endpoint | `glm-5.3[1m]` |
| `kimi-k3` | Kimi Code 0.31.1 | `kimi-code/k3` |
| `codex-terra-high` | Codex CLI 0.147.0 | `gpt-5.6-terra`, high effort |
| `codex-sol-high` | Codex CLI 0.147.0 | `gpt-5.6-sol`, high effort |

All candidates received the same packet hash for a given task:

| Task | SHA-256 |
|---|---|
| Historical | `84a5b60b5d6cddbce917d7400cb1bedfeb94bacdcd5bbdcc2b813494adfa017f` |
| Research | `5f5be999fa7c4de2a81a4ea024a288e4d73949ffcf5ebbee8af70453145e833d` |
| Daily Ops | `97f40904a57a5c9560deaf1d64146c83c09ebfab92c1f8a6ad2b4ec1ae9c7e78` |

The worktrees were isolated with Bubblewrap. Native web search/fetch was
disabled. Candidate code could read and write only its worktree and use a
bounded command surface. Canonical repositories, credentials, Gmail, Trello,
and production data were not exposed to candidates. No live writes or deploys
were permitted.

## Context-window facts and uncertainties

### Main pass

- The harness labeled and requested **65,536 tokens** for all 27 runs.
- The context ladder was **not run**.
- Ollama requests included `options.num_ctx = 65536`, `temperature = 0`, and a
  30-minute keep-alive. The response records do not independently report the
  effective allocated KV context, so 65,536 is verified as requested, not
  measured as effective.
- Codex was launched with `model_context_window=65536` and high reasoning.
- Claude Code was given `CLAUDE_CODE_AUTO_COMPACT_WINDOW=65536`. Z.AI reported
  the underlying GLM-5.3 model context as 1,000,000 tokens, but Historical ended
  with `rapid_refill_breaker`: autocompaction refilled to its limit within three
  turns, three times. Thus “64K requested,” “1M model capacity,” and “effective
  agent working context” are different facts.
- The Kimi prompt stated 65,536, but this harness did not record an independent
  effective-context value.
- Exact Ollama model digests and quantization were required by the original
  design but are absent from these stored run records. They must be captured in
  a corrected run.

### Focused canary

The later two-model canary explicitly used:

- `num_ctx = 8192`
- `num_predict = 1024`
- `temperature = 0`
- `think = false`
- a readiness prompt before execution
- exactly three offered tools: `read_file`, `write_file`, `run_test`
- a fully specified two-file task requiring one minimal normalization fix

This canary was intended to answer “can this served model perform a basic coding
tool loop at all?” It was not a quality benchmark.

## What happened in the 64K main pass

| System | Historical | Research | Daily Ops | Interpretation |
|---|---:|---:|---:|---|
| Qwen3 Coder 30B | completed, no diff | completed, 89 changed lines | completed, 129 changed lines | Most usable Ollama coding behavior in this pass; Research artifact still failed the flawed hidden import tests. |
| Qwen3 Coder Next | 80-step cap, no diff | 80-step cap, 131 lines | 80-step cap, no diff | Repeated invalid/tool-loop behavior; did not terminate cleanly. |
| GPT-OSS 120B | Ollama HTTP 500 | Ollama HTTP 500 | Ollama HTTP 500 | Main-pass failure was serving/runtime-related; later 8K canary proves basic tool use works. |
| Gemma4 26B | completed, no diff | completed, 55 lines | 30-minute timeout, 287 lines | Could inspect and modify code, but completion and test reliability were uneven. |
| GLM-4.6V Flash 9B | 30-minute timeout, no diff | stopped with no diff | 30-minute timeout, no diff | Existing non-native JSON tool path did not yield useful main-task work. Later native-tool canary exposed massive duplicate calls. |
| Z.AI GLM-5.3 | process exit, no diff | 30-minute timeout, 36 lines | 30-minute timeout, 551 lines | Did substantial work where time allowed; arbitrary timeout and compaction behavior prevent a fair quality conclusion. |
| Kimi K3 | quota failure after 289 lines | immediate quota 403 | immediate quota 403 | Only Historical contains model work; the other two are quota failures, not model results. |
| Codex Terra High | completed, 409 lines | completed, 38 lines | completed, 485 lines | Fast and compact; passed 2/7 Historical focused tests but introduced more broad regressions than Sol. |
| Codex Sol High | completed, 739 lines | completed, 104 lines | completed, 897 lines | Broadest and most defensive implementations; missed all seven exact Historical assertions but preserved more broad tests. |

The 30-minute cap was not appropriate as a universal capability boundary. It
was terminal by policy and no timed-out run was retried. Future modular trials
should record time-to-module and stop only on a task-specific ceiling.

## Scoring validity

### Historical

The focused acceptance tests were legitimate tests of exact-source delivery and
replay fencing:

- Sol: 0/7 focused; 739 broad tests passed, 5 failed.
- Terra: 2/7 focused; 723 broad tests passed, 18 failed.
- Kimi: 1/7 focused before quota exhaustion; 730 broad tests passed, 6 failed.
- Other systems: 0/7 focused in their recorded artifacts.

Terra's two focused passes do not mean it completed the repair. It correctly
implemented stable timestamp/event-ID ordering and bounded one source to two
transport attempts. Both Codex implementations missed exact source propagation
through `floor_forward_work_order.py` and several exact receipt/fence contracts.
Sol's lower focused count but better broad regression preservation is why raw
pass count alone is misleading.

### Research and Daily Ops

The hidden suites imported hard-coded, undisclosed package/module names. Several
valid alternative layouts failed during test collection. Therefore the recorded
“0 hidden tests passed” means the tests could not import the implementation; it
does not mean the implementation was exercised and every behavior failed.

Self-authored baseline tests are useful but not a neutral ranking. Examples:

- Sol Daily Ops: 64 passed.
- Terra Daily Ops: 58 passed.
- Qwen3 Coder 30B Daily Ops: 62 passed.
- Sol Research built a wheel and its focused recheck passed 15 tests.
- Terra Research built a wheel and passed 9 tests.

Manual inspection found Sol generally more defensive and comprehensive, while
Terra was smaller, faster, and had some locally better design choices, notably
hash-based stable Research source IDs.

## Focused GPT-OSS and GLM canary evidence

### `gpt-oss:120b`

- Readiness response: `MISSING module.py` and `MISSING test_module.py`. This was
  a reasonable request for access/content before acting, although the next
  prompt made the tool access explicit.
- Execution: read each file once, wrote the minimal correction once, ran the
  test once, and stopped.
- Total tool calls: 4.
- Result: `1 passed`.
- Wall time: 38.30 seconds, including a roughly 24.6-second initial model load.

Conclusion: GPT-OSS 120B can perform a disciplined native tool loop through
Ollama at 8K. Its three 64K HTTP 500 failures require a serving/context/resource
diagnosis, not rejection of the model.

### `MedAIBase/GLM-4.6V-Flash:9b`

- Readiness response: `READY`.
- It read both files and produced the correct minimal fix.
- Result: `1 passed`.
- Wall time: 146.89 seconds.
- Total tool calls: **167**:
  - 2 `read_file`
  - 1 `write_file`
  - **164 `run_test`**
- Multiple tool calls were emitted in single assistant responses despite the
  prompt saying “at most one tool call per turn.”

Conclusion: GLM-4.6V Flash is capable of the code edit, but this model/template/
parser/backend/harness combination is not a safe coding-agent loop. The evidence
does not isolate which layer caused the duplication.

## Backend discovery: Ollama versus `llama-server`

The relevant community source is:

- <https://github.com/hogeheer499-commits/strix-halo-guide>
- <https://github.com/hogeheer499-commits/strix-halo-guide/blob/main/STRIX_HALO_LOCAL_LLM_SETUP.md>

Its backend-selection table recommends:

- Ollama/Vulkan/RADV for easiest private local chat and first success.
- `llama-server` for a local API, several tools, long-context tests, MTP, and
  server experiments.
- direct `llama.cpp`/`llama-server` when reproducible control and measured
  generation performance matter more than easiest setup.

The official llama.cpp server documentation says `llama-server` provides an
OpenAI-compatible HTTP API, configurable context, performance timings, and
function calling. Its function-calling documentation supports native handlers
and a generic fallback; parallel tool calls are disabled by default unless the
client explicitly enables them:

- <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- <https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md>

### Correct inference

Our workload—multi-turn coding agents, bounded tools, long context, explicit
metrics, and repeatability—matches the guide's stated `llama-server` use case
more closely than its stated Ollama use case. Therefore a `llama-server` A/B
test is warranted.

### Inferences not yet justified

- “Ollama does not support coding agents.”
- “Ollama caused GLM's 164 repeated test calls.”
- “`llama-server` will parse this GLM model correctly.”
- “The Ollama 64K GPT-OSS failures were definitely out-of-memory failures.”
- “Switching the backend will improve model reasoning quality.”

Those require controlled evidence.

## Questions for an independent research pass

Please investigate and cite primary sources wherever possible:

1. For each exact model/quant used here, what chat template and tool-call parser
   does Ollama select? Is native tool calling supported, generic, or absent?
2. Does the installed Ollama version have known issues with GLM-4/GLM-4.6V
   emitting or parsing repeated/parallel tool calls?
3. Does Ollama enable or accept parallel tool calls implicitly for `/api/chat`?
   Can the client explicitly disable them?
4. What server log or API field proves the effective `num_ctx`, KV-cache size,
   GPU/CPU placement, and reason for an HTTP 500?
5. At 65,536 context, what memory should `gpt-oss:120b` require for weights,
   KV cache, compute buffers, and Vulkan overhead on a 128GB Strix Halo system?
6. Can the exact installed Ollama model blobs be reused by `llama-server`, or
   must canonical GGUF files and projector/template assets be obtained?
7. Does llama.cpp have a native GLM-4.6V/GLM-4 tool-call handler? If not, which
   Jinja template or generic handler is appropriate?
8. How should reasoning content be preserved between turns for GPT-OSS and GLM
   under `llama-server`?
9. Which exact llama.cpp build and Vulkan flags are validated on Ryzen AI MAX+
   395 / Radeon 8060S, and how should CPU fallback be recorded?
10. What minimal A/B protocol will distinguish model behavior from parser,
    template, backend, and harness behavior?

## Proposed Ollama / `llama-server` A/B protocol

Do not repeat the full benchmark first. Freeze the existing results, then:

1. Select GPT-OSS 120B and GLM-4.6V Flash first because their failures are most
   diagnostic.
2. Resolve and record the same underlying model weights/quantization, chat
   template, stop tokens, and tool schema for both backends.
3. Record software commit/version, model SHA-256/digest, command line, Vulkan
   device, power mode, resident memory, and effective context.
4. Run the existing two-file canary at 8K, then 16K, then 32K, and only then 64K.
   Stop increasing context at the first serving failure.
5. Send one tool result at a time. Reject more than one call if parallel calls
   were not explicitly requested. Record the raw unparsed assistant output and
   parsed tool calls.
6. Run three deterministic repetitions per backend/context where supported.
7. Compare correctness, unique versus duplicate tool calls, invalid calls,
   prompt/decode speed, time to first token, peak memory, stop reason, and
   whether the model asks a legitimate clarification.
8. Only after the tool loop is stable, give one small repository module with a
   research/clarification phase and owner answers before implementation.

No driver reinstall, package replacement, reboot, canonical-repository change,
or Whisper installation is part of this diagnostic.

## Repository and evidence status

The benchmark currently exists locally at
`/home/cdc/Storage/projects/coding-benchmark`. It is initialized as Git on
branch `main`, but has **no commits and no remote**. It is not presently a
GitHub repository.

The working tree must not be published as-is:

- `profiles/kimi/` is not fully ignored and contains local profile/session
  material.
- Codex and Z.AI profile areas also require a secret and identity audit.
- `results/`, `runs/`, and `hidden/` are ignored, so a normal push would omit
  both useful evidence and acceptance material.
- Raw transcripts may contain local paths, provider diagnostics, prompt data,
  or account-related metadata even when credential values are absent.
- Candidate worktrees derive from private/canonical project snapshots and must
  not be published without a code/provenance review.

## Recommended public GitHub boundary

Creating a public repository is worthwhile if the goal is to collaborate with
the Strix Halo and local-inference communities over time. Publish a sanitized
benchmark framework, not this working directory.

Suggested initial contents:

- benchmark methodology and limitations;
- generic canary tasks created specifically for public use;
- Ollama and `llama-server` adapters;
- JSON schemas for environment, run, metric, and result records;
- redacted aggregate results plus selected raw parser transcripts;
- reproduction commands and hardware/software manifests;
- issue templates for new model/backend results;
- contribution guide requiring digests, backend versions, context proof, and
  raw-log redaction;
- a clear license and security policy.

Keep private:

- all provider profiles, OAuth material, credentials, and account metadata;
- Floor/Tessera/Daily Ops source snapshots and hidden tests derived from them;
- private task packets or transcripts containing private code/context;
- canonical-repository worktrees.

A good public first milestone is the generic two-file canary plus a sanitized
backend A/B runner and results schema. Historical Floor, Research, and Daily Ops
can remain private until replaced by purpose-built public tasks.

## Evidence files in the local benchmark

- `benchmark/config.py`: roster and nominal contexts.
- `benchmark/run_matrix.py`: harness commands and 64K request settings.
- `benchmark/ollama_agent.py`: Ollama tool loop and `num_ctx` request.
- `benchmark/simple_canary.py`: focused 8K canary contract.
- `results/canary-gpt-oss-120b.json`: successful disciplined GPT-OSS trace.
- `results/canary-glm-4.6v-flash-9b.json`: correct edit plus 164 duplicate tests.
- `results/*.json`: per-run timing, output, diffs, and transcripts.
- `results/scores.json`: current scorer output; Research/Daily functional
  columns must not be treated as valid capability scores.
- `results/timing-contamination.json`: two owner-started `translategemma:12b`
  overlap records; affected efficiency timing must be excluded.
