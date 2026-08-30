# Two-model local evaluation pilot — 2026-08-30

## Scope and result

This authorized sequential pilot evaluated the two exact local GGUF artifacts
named below on the `gallery` and held-out `code_review` task families. Translation
was deferred and did not block the pilot. One model server was resident at a
time; each server bound only to `127.0.0.1`. Persistent Unsloth Studio remained
stopped throughout.

All four scheduled cells reached durable terminal evidence. This is a
dimension-by-dimension pilot record, not a single composite ranking.

| Model | Gallery | Code review | Broader-suite decision |
| --- | --- | --- | --- |
| Qwen3.8-Flash-Next UD-Q3_K_XL | `infrastructure_blocked` | `accepted` | Do not advance until browser-host acceptance can run; native-tool and review behavior warrant a rerun. |
| Llama-3.3-Nemotron-Super-49B-v1 UD-Q6_K_XL | `server_compatibility_blocked` | `server_compatibility_blocked` | Do not advance under this native OpenAI-tool/template configuration. |

## Exact artifacts

| Model | Hugging Face repository and installed revision | Exact GGUF identity | Local artifact bytes | Cache-object SHA-256 identity |
| --- | --- | --- | ---:| --- |
| Qwen | `unsloth/Qwen3.8-Flash-Next-GGUF` at `c8b5954a88c2775c546b92593eda40ea041d3176` | `Qwen3.8-Flash-Next-UD-Q3_K_XL-00001-of-00003.gguf`, `...00002-of-00003.gguf`, `...00003-of-00003.gguf` | 10,946,624 + 49,983,253,824 + 39,992,153,376 | `f2ef4328929d8b8c8930e2856eef52128dd4ce3425302f04bc3c657431cc4c49`, `7d230e7c9421d868b89eebaf23033af0ea1a4e046956df00fb156814fb62346e`, `21d4f90f9cd7b7c3a1582667c20cb22f7b03de895b88a23bb20aaeaa44f2c199` |
| Nemotron | `unsloth/Llama-3_3-Nemotron-Super-49B-v1-GGUF` at `6c679d12e88815cf6c66cf627b46ea66acfdeb4d` | `Llama-3_3-Nemotron-Super-49B-v1-UD-Q6_K_XL.gguf` | 43,417,787,904 | `6fbd8b97e11cbfa3ff58014ccc0d9d023ee5475e89660f4961602dd03fc59fed` |

The `v1` Nemotron repository above is intentional; no `v1_5` artifact was
substituted.

## Serving and harness configuration

- Server: local `llama-server` `0.3.0-dev`, build `10687`, commit `92b19177a`, Vulkan backend; loopback-only disposable instances.
- Both: `--ctx-size 65536 --gpu-layers 999 --flash-attn on --jinja --reasoning on`.
- Qwen: additionally `--reasoning-effort xhigh --reasoning-preserve`; request sampling `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0`, presence penalty `0`, repeat penalty `1`, `max_tokens=8192`.
- Nemotron: reasoning-on; request sampling `temperature=0.6`, `top_p=0.95`, `max_tokens=8192`.
- Candidate interface: native OpenAI-compatible function tools only. The harness exposed bounded workspace file listing/search/read/write/patch/command tools. No textual tool-call adapter was substituted.
- Candidate environment: isolated Node 24 and the local Playwright browser path were explicitly passed to subprocess tools.

Raw trajectories, model reasoning, candidate output, held-out fixture/gold data,
and private workspace diffs remain Git-ignored local evidence; they are not
included in this tracked report.

## Native-tool compatibility

| Model | Result | Evidence |
| --- | --- | --- |
| Qwen | Passed | The Qwen canary performed a native read and returned the expected canary token. The scored runs also recorded 53 gallery and 7 review native tool calls. |
| Nemotron | Blocked | The fresh canary made zero native tool calls and returned a generic refusal to access the filesystem. The two scheduled task cells repeated that behavior. |

## Scheduled-cell evidence

| Cell | Autonomous/supervised trajectory | Terminal classification and hard outcome | Model-turn wall time | Tool calls / intervention record |
| --- | --- | --- | ---:| --- |
| Qwen gallery | The candidate eventually implemented a full local app after extended inspection. It passed its own TypeScript typecheck and Vite production build. | `infrastructure_blocked`: Chromium could not launch because host shared libraries were absent. Installing OS packages was prohibited, so no valid browser acceptance or screenshots could be produced. This is not a model failure. | 00:41:27 | 53; `I1`, `I2`, `I3` ×2, then `I0` for the browser dependency. |
| Qwen code review | Candidate inspected only the supplied fixture, ran focused behavior checks, and returned five bounded findings. | `accepted`: blind private scoring completed. Recall `1.00` (3/3), precision `0.60` (3 credited defects across 5 findings), 3 non-gold findings. Required fields and the eight-finding ceiling were observed. | 00:02:08 | 7; none. |
| Nemotron gallery | Fresh native-tool canary had already failed. The scheduled cell made no tool calls, did not read the workspace, and created no files. | `server_compatibility_blocked`: it emitted a generic hypothetical implementation narrative rather than operating on the isolated task. | 00:06:32 | 0; none. |
| Nemotron code review | The scheduled cell made no tool calls and did not inspect `service.py`. | `server_compatibility_blocked`: it fabricated hypothetical findings for paths not present in the fixture. Blind score: recall `0.00`, precision `0.00`, 8 non-gold findings. | 00:02:43 | 0; none. |

The Qwen gallery candidate's autonomous source work and private diff are
retained, but visual screenshots are intentionally absent: the browser failed
before page execution. Any future screenshot paths must be generated only by a
rerun after separately authorized host dependency remediation.

## Runtime and evaluation observations

- The browser failure is host infrastructure, not a page failure: Playwright
  reported missing `libatk`, `libatspi`, `libxdamage`, and `libasound` family
  dependencies before Chromium launched. No package, driver, network, storage,
  or persistent service was modified.
- Qwen showed substantial planning/refactoring latency before implementation;
  factual I1, criterion I2, and two bounded I3 messages were logged under the
  authorized supervisor policy. It then produced source, passed typecheck, and
  built successfully. The browser blocker prevented final gallery acceptance.
- Nemotron's local performance was approximately 5.2 generated tokens/s in
  these short calls, but the decisive issue was native tool/template
  incompatibility, not throughput.
- All disposable model servers were stopped at the end. No port `18901` or
  `18902` listener remained.

## Harness changes and validity

The pilot branch includes three pre-run harness hardenings made to prevent an
invalid comparison:

- bounded workspace listings, preventing `node_modules` from flooding tool
  results (`e488dab`);
- explicit Node/Playwright environment propagation to candidate subprocesses
  (`e161b29`);
- a per-run advisory turn lock, preventing overlapping candidate turns
  (`9b1ad20`).

Those changes made the Qwen rerun serial and inspectable. They do not repair a
model or hide the Nemotron native-tool failure. The harness is valid for a
future full suite only after (1) separately authorized browser host dependency
remediation and a fresh gallery validation rerun, and (2) a documented
native-tool template compatibility resolution for any model that fails the
canary. Neither action was taken in this pilot.

## Next action

Do not start the broader suite automatically. Obtain a new Owner instruction
for the narrowly scoped browser-dependency remedy and/or an explicitly labelled
Nemotron template/adapter investigation, then rerun the affected cells under
the same recorded contracts.
