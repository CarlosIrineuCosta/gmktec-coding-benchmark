# Pilot execution handoff — 2026-08-30

## /goal

Run the authorized two-model GMKtec pilot to valid terminal evidence for the **gallery generation** and **code-review** lanes. Remain actively in the supervisory control loop throughout candidate execution. Do not stop after preparing a server, launching a watcher, producing a partial artifact, or reaching an ordinary branch/PR boundary. The pilot is complete only when all four scheduled model/task runs have a valid terminal classification and preserved evidence, or when a genuinely unrecoverable/destructive boundary is documented for an individual run and the remaining independent runs have still been attempted.

This is an **execution authorization**, not another setup request.

## 1. Authoritative branch and precedence

Use branch:

`agent/local-model-evaluation-pilot-20260830`

It was created from completed setup commit `31b760fb874fde1766d6c9428a025daa19b625b9`.

Do not stop because `main` is protected and do not ask the owner to bypass branch protection. Pilot execution may proceed entirely on this branch. Commit and push compact/sanitized project changes and reports to this branch. Raw/private evidence remains under `data/private/` and is not pushed.

Read first:

1. `docs/intake/gpt/2026-08-30/local-model-evaluation-spec.md`
2. `docs/architecture/2026-08-30-supervised-unsloth-evaluation.md`
3. `docs/architecture/2026-08-30-evaluation-setup-contract.md`
4. this handoff
5. `tasks/local-model-evaluation/pilot.json`

The root `README.md` and legacy August-16 execution material do not override these dated campaign documents where they conflict.

## 2. Pilot selection is now explicit

The owner delegated pilot selection/execution to the GPT coordinator. The pilot pair is now fixed in `tasks/local-model-evaluation/pilot.json`.

### Candidate A — large new Qwen

- Repository: `unsloth/Qwen3.8-Flash-Next-GGUF`
- Quant: `UD-Q3_K_XL`
- Expected form: multi-shard GGUF under the exact installed HF snapshot
- Do **not** substitute Q2, Q4, another Q3 flavor, or another Qwen model.

### Candidate B — medium/heavy Nemotron

- Repository: `unsloth/Llama-3_3-Nemotron-Super-49B-v1-GGUF`
- Quant: `UD-Q6_K_XL`
- Expected artifact: `Llama-3_3-Nemotron-Super-49B-v1-UD-Q6_K_XL.gguf`
- Do **not** substitute the 4B Nano, 30B Nano, 3.5 Lightning, Q4, Q8, or another Nemotron.

The 4B Nano and other Nemotron variants are candidates for the later full suite, not this pilot.

## 3. Translation does NOT block this pilot

The translation lane is deferred until the owner supplies source text.

Do not wait for it.
Do not ask for it.
Do not run translation in this pilot.

The pilot consists of exactly four scored runs:

1. Qwen3.8-Flash-Next Q3 — gallery
2. Qwen3.8-Flash-Next Q3 — code review
3. Llama-3.3-Nemotron-Super-49B Q6 — gallery
4. Llama-3.3-Nemotron-Super-49B Q6 — code review

Runs are sequential; only one candidate server/model should be resident for benchmark execution at a time.

If artifact availability makes the listed order impractical, you may reorder the four runs without owner approval, but record the deviation. Do not substitute a model or quant.

## 4. Authority to proceed without repeated owner confirmation

For this pilot you are explicitly authorized to perform ordinary, reversible execution work needed to finish the four runs, including:

- inspect the current HF/Unsloth cache and resolve exact snapshots/shards;
- hash model artifacts where practical;
- complete/download an exact selected artifact into the existing canonical `/home/cdc/Models/Unsloth/huggingface` cache if it is incomplete or absent;
- create disposable worktrees/directories under the benchmark project/private data boundary;
- install routine project-local test/harness dependencies in an isolated project environment if missing;
- start/stop disposable loopback-only Unsloth/llama.cpp candidate servers on non-conflicting ports;
- run candidate tasks, tests, Playwright acceptance, screenshots, and evidence capture;
- make harness repairs when the harness itself is demonstrably defective, provided those repairs are recorded and do not silently alter already-scored candidate conditions;
- retry an infrastructure/server launch when the failure is I0 infrastructure rather than model behavior;
- commit/push sanitized benchmark code, configuration, reports, and handoffs on the pilot branch.

Do not ask the owner for permission at each ordinary step.

Still stop/escalate before kernel, firmware, BIOS, Mesa/RADV, partition/storage-layout, Tailscale, persistent Studio authentication, public network exposure, destructive unrelated-file changes, or other system-level mutations outside this bounded experiment.

## 5. Fresh preflight before candidate inference

Before the first candidate turn:

1. capture a fresh machine/runtime/model inventory with the setup tooling;
2. record current Unsloth version and exact bundled llama.cpp build/commit;
3. verify `llama-server --list-devices` still exposes `Vulkan0: Radeon 8060S Graphics (RADV STRIX_HALO)`;
4. verify persistent Studio on 18888 remains healthy and do not repurpose its port;
5. resolve each selected model to exact local repository snapshot/revision, GGUF filename(s), bytes, and SHA-256 where practical;
6. if a selected artifact is still downloading, do not treat that as a benchmark failure and do not substitute another artifact;
7. verify the private gallery materialization and code-review gold fixture exist;
8. run the mock/unit suite once after checking out this branch.

If exact selected model bytes are missing, obtain **only the selected artifact** through the current Unsloth/Hugging Face storage path. Do not create a new model/cache namespace.

## 6. Complete the thin real execution controller if setup left only primitives

The setup branch contains lifecycle/session/evidence primitives. In particular, `OpenAICompatibleSession.one_turn()` is a one-turn primitive and explicitly states that callers own the active loop.

Therefore, before the first scored run, implement the **smallest auditable real runner/controller needed to execute a multi-turn candidate task** if no such controller already exists.

It must:

- construct the task conversation from the canonical packet;
- send one assistant turn to the disposable OpenAI-compatible endpoint;
- execute only the bounded workspace tools;
- append tool results to the conversation using the server/model's expected OpenAI-compatible format;
- continue model/tool turns until the model reaches a candidate-defined completion point, requests clarification, or enters a supervised condition;
- preserve every model turn/tool call in private evidence;
- expose state to Codex so Codex, not an autonomous watchdog, makes supervision decisions;
- allow a logged I1/I2/I3 supervisor message to be inserted as a normal subsequent user/supervisor turn;
- never allow I4 implementation assistance;
- avoid hidden autonomous 'fix the candidate' behavior.

Validate that controller with fake/mock responses first. This is the final bridge from setup primitives to real execution, not a reason to declare setup complete again and stop.

## 7. Serving policy

Use the installed Unsloth/llama.cpp Vulkan stack and disposable loopback servers. Do not make Ollama a pilot lane.

Initial pilot context ceiling: **65,536 tokens** for both models. The tasks should naturally use much less. This is not a context-window benchmark.

If a selected model cannot serve at 65,536 because of a genuine memory/runtime constraint:

1. classify the failed attempt as serving/runtime evidence, not model-quality failure;
2. inspect the exact reason;
3. choose the largest stable context that comfortably contains the real task;
4. record the deviation;
5. continue the run.

Do not terminate the whole pilot because one model has a serving/configuration issue.

Do not disturb the persistent Studio management service on port 18888 except to inspect health.

## 8. Model-native configuration

Do not force both candidates into an artificial identical reasoning policy. Record the full effective configuration.

### Qwen3.8-Flash-Next

Use **thinking mode ON** for this pilot and preserve thinking across multi-turn agent work if the current Unsloth/llama.cpp template supports it correctly.

Prefer the model's documented thinking-mode sampling as supported by the installed runtime:

- temperature `1.0`
- top_p `0.95`
- top_k `20`
- min_p `0.0`
- presence_penalty `0.0`
- repetition_penalty `1.0`

Use a documented/supported `reasoning_effort`; prefer `xhigh` as the model-native default for serious agentic work unless the installed llama.cpp/Unsloth integration demonstrably maps a different value. Record whether `enable_thinking`, `preserve_thinking`, and `reasoning_effort` actually reach the chat template. Do not merely put unsupported fields in JSON and assume they took effect.

If the runtime cannot express one of these knobs, record the limitation and use the closest native supported configuration rather than inventing a compatibility layer.

### Llama-3.3-Nemotron-Super-49B-v1

This model supports reasoning and non-reasoning modes via its prompt/template. For the **gallery coding run**, use its documented reasoning-on configuration when compatible with native tool use; recommended sampling for reasoning-on is temperature `0.6`, top_p `0.95`.

For the **code-review run**, reasoning-on is also preferred for depth unless the model's native tool/template contract makes reasoning-off materially more compatible. If you change reasoning mode for compatibility, record it as part of the experimental unit and explain why.

Do not silently replace the primary native OpenAI-compatible tool contract with the model card's benchmark-specific textual `<TOOLCALL>` format. If native tool calls fail, classify that first. A later explicitly labeled adapter may be tested separately; it must not erase the native-tool result.

## 9. Pre-run native-tool compatibility canary

Before each candidate's first scored task, perform one **unscored serving/tool compatibility canary** with the exact candidate artifact and the same primary harness:

- small disposable workspace;
- one read tool;
- one minimal deterministic task;
- bounded output;
- verify the model can produce a usable tool call and consume its result;
- tear down the canary state.

This canary is not a quality score. It answers only whether the serving/template/tool contract is operational.

If the canary fails:

1. determine whether this is server/template/harness incompatibility or obvious model behavior;
2. make only documented native-configuration corrections;
3. retry the canary once after a real I0/harness correction;
4. if native tool compatibility remains unavailable, preserve that result and continue to any task lane that can still be evaluated validly without fabricating a hidden advantage.

Do not loop indefinitely on compatibility.

## 10. Gallery run procedure

For each model:

1. create a fresh isolated gallery worktree/fixture;
2. copy/materialize the exact same 12 local public-domain images and manifest;
3. deliver the canonical gallery packet once as the Stage-A task;
4. give the model the bounded workspace tools;
5. allow it to inspect/edit/run tests/build as needed;
6. Codex actively supervises but gives no substantive help during Stage A;
7. when the model declares completion or stops making productive progress, run the objective acceptance suite;
8. capture standardized desktop/mobile screenshots;
9. if acceptance fails, enter Stage B using I1 -> I2 -> I3 only as warranted;
10. allow the model to continue after each intervention;
11. rerun acceptance after candidate changes;
12. record autonomous result separately from final supervised result;
13. capture final diff and evidence;
14. terminate the disposable model server and verify its port/process are gone before the next candidate.

Do not use Codex aesthetic judgment as a hidden pass/fail gate. Preserve screenshots for Charles's later visual rating.

## 11. Code-review run procedure

For each model:

1. create/reset the exact same review fixture visible to the candidate;
2. ensure gold/hidden data remain inaccessible;
3. deliver the canonical review packet;
4. candidate acts as reviewer, not implementer;
5. bound the number of findings according to the packet;
6. score against private gold only after candidate completion;
7. compute recall/precision/false positives/severity/location/explanation metrics defined by the setup;
8. Codex does **not** provide substantive review hints in this lane. Infrastructure correction is allowed, but I2/I3 assistance that reveals defects invalidates the autonomous review and must not be used to manufacture a better score;
9. preserve the candidate's exact review output and scored result;
10. terminate the candidate server cleanly.

## 12. Active Codex supervision — mandatory behavior

A Python watcher, tmux process, shell loop, systemd service, or sleeping monitor may collect state but is not the supervisor.

During candidate execution Codex itself must remain responsible for the run.

At approximately five-minute checkpoints, or earlier on meaningful events, Codex must actively inspect and reason about:

- candidate/server process health;
- latest model turn and whether generation is genuinely active;
- latest tool calls;
- worktree diff/mtime and meaningful source changes;
- test/build state;
- repeated command/tool patterns;
- malformed tool calls;
- false-success declarations;
- whether an I0/I1/I2/I3 action is warranted.

Record a supervisory decision at each checkpoint.

**Do not execute `sleep 300` as the conceptual supervision strategy.** A telemetry helper may sleep; Codex must resume reasoning at each checkpoint and continue until the run reaches a valid terminal state.

If the Codex interface requires a foreground polling command to regain control, structure the process so Codex periodically regains control and evaluates state rather than delegating indefinitely to a child.

## 13. Intervention budget and recovery

Use judgment rather than an arbitrary wall-clock timeout.

A reasonable default recovery sequence for gallery is:

- first actionable failure: I1 raw/minimally interpreted diagnostic;
- persistent unmet requirement: I2 criterion reminder;
- persistent coherent but misdirected implementation: I3 directional hint;
- at most two I3 interventions unless there is clear continuing progress that justifies one additional attempt.

Do not use I4.

Time is a metric, not a universal terminal boundary.

Two consecutive supervision checkpoints with no meaningful progress trigger an explicit stall decision, not automatic kill.

If the model remains in a genuine no-progress loop after allowed recovery, classify it terminally and continue with the next independent run.

## 14. Failure isolation

Under no circumstance should one failed candidate/task abort the remaining pilot schedule unless the failure reveals a shared harness defect that makes later results invalid.

If a shared harness defect is found:

1. stop scoring;
2. repair the harness;
3. validate with mocks/canary;
4. determine whether already-completed scored runs were affected;
5. rerun only invalidated runs, explaining why;
6. continue the pilot.

A candidate-specific server failure, tool incompatibility, bad output, loop, or inability to finish is not a reason to stop the whole pilot.

## 15. Evidence and reports

For every scored run preserve the setup-defined private evidence, including manifest, request, server configuration, events, interventions, metrics, acceptance, summary, and final diff where applicable.

At the end of the pilot write a sanitized tracked report under:

`docs/reports/2026-08-30-two-model-pilot.md`

The report must keep dimensions separate rather than producing one opaque score. Include:

- exact artifact identities/revisions/hashes;
- exact serving/template/reasoning configuration;
- native-tool canary result;
- autonomous completion;
- supervised completion;
- intervention counts/classes;
- hard acceptance outcome;
- wall time;
- tool-call counts and pathological/repeated behavior;
- code-review precision/recall/false positives;
- gallery screenshot paths/references for owner review;
- serving/runtime anomalies;
- whether each candidate should advance to the broader suite;
- any harness changes made during execution and their effect on validity.

Do not produce a single winner score.

## 16. Completion condition

Do not stop after preflight.
Do not stop after implementing the controller.
Do not stop after a successful canary.
Do not stop after the first model.
Do not stop after the first task.
Do not stop because a model fails.
Do not stop because `main` is protected.

The execution goal is satisfied only when all four scheduled pilot runs have a valid terminal classification and the pilot report/evidence are written and pushed to the pilot branch, subject only to the explicit destructive/system-level escalation boundary above.

At that point report to Charles:

- pilot branch HEAD;
- four terminal run classifications;
- concise autonomous vs supervised results;
- intervention counts;
- major runtime/tool pathologies;
- gallery screenshot locations;
- code-review metrics;
- recommendation on whether the harness is valid for the full suite;
- exact next action, but do not start the full suite without a new owner instruction.
