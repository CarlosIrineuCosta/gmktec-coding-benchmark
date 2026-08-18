# GMKtec Unsloth Qwen3.8-27B Execution Record

**Date:** 2026-08-18
**Status:** executed; corrected GLM-5.3 and Kimi K3 full-core rerun added 2026-08-18; no Q4 variant tested
**Scope:** Unsloth Studio/CLI serving of Qwen3.8-27B Q8_0, UD-Q6_K_XL, and UD-Q5_K_XL on GMKtec. This is a controlled experiment, not a production promotion.

## Decision answer

Qwen3.8-27B cannot yet become the default practical local coding model for autonomous repository work on this machine. The strongest practical quant in this run is **UD-Q5_K_XL**, because it alone made the second-pass browser simulation operational and it completed the 128K retrieval contract. That is useful evidence for local exploratory generation and bounded two-pass browser work.

It is not sufficient evidence for local-first autonomous coding: the selected Q5 route exhausted its fresh agentic substitution task without editing the fixture, and direct independent validation failed both acceptance tests. The properly executed Terra and GLM-5.3 comparisons each made a test-valid patch and passed both supplied tests.

Current route posture:

- **Local-first with remote fallback:** Q5 for bounded canaries, controlled local generation, and inspected browser prototypes; every result needs functional validation.
- **Remote still required:** fresh repository diagnosis and autonomous edit/test/repair tasks until Q5 succeeds repeatedly under a corrected agent harness.
- **Not selected:** Q6 for the two-pass browser repair, because two identical attempts produced only a 365-byte response rather than a replacement page. Q8 made a full replacement page but it remained functionally frozen.

## Pinned environment and artifacts

- Unsloth release: `v0.1.800-beta`, commit `a8be2a8`.
- Installer SHA-256: `38f6f139a264aaa737f62267c3ad57ecd06a89f92757c45b611b16f8e4546224`.
- Resolved CLI: `unsloth 2026.8.18`.
- Model revision: `f1bfb127c64f7072bdd2cad55f258b9c8b2910fe`.
- Backend: native Unsloth llama-server on ROCm, native template and MTP (`draft-mtp`, maximum two draft tokens). One model was loaded at a time; the existing Ollama service was not changed.
- Quants: Q8_0, UD-Q6_K_XL, UD-Q5_K_XL. The planned Q4 exclusion was respected.

Raw runner evidence is retained under the restricted experiment root `/srv/llm-runner/experiments/unsloth-qwen38-27b-20260818`. This report intentionally contains no API keys or raw server logs.

## Core run

Each quant ran the same fixed-sampling core suite at 64K: three repetitions of the restricted Python canary, two browser one-shots, and an isolated agentic coding canary. Total suite wall time was strikingly close despite the smaller quant:

| Quant | Core-suite wall time | Restricted-canary mean | Agentic canary |
| --- | ---: | ---: | --- |
| Q8_0 | 11m 58s | 28.64s | 35.353s; 5 turns, 6 tool calls, 1 write |
| UD-Q6_K_XL | 12m 17s | 24.97s | 31.366s; 5 turns, 6 tool calls, 1 write |
| UD-Q5_K_XL | 11m 17s | 17.93s | 31.219s; 5 turns, 6 tool calls, 1 write |

The restricted canary favored Q5, but this did not translate into a material whole-suite advantage. Each model's initial agentic hidden-test invocation had a harness-path error (`src` was not importable because the test ran outside its worktree). The test was corrected to run from the worktree with `PYTHONPATH=.`; all three then passed the two hidden tests. Those corrected results are valid for the narrow canary only.

## Browser one-shots and single equal repair pass

The transparent-volcano simulation and DOOM/raycaster one-shots were intentionally retained as qualitative tests. All first-pass volcano pages were visually substantive but dormant. Browser validation established that controls received clicks and no meaningful JavaScript error occurred, yet time, pressure, particles, and telemetry stayed fixed because the generated source defined update functions without ever starting an animation loop.

Each quant then received the exact same repair brief plus its own frozen generated source: start a `requestAnimationFrame` loop, use stable delta time, invoke update/render, and preserve the page's controls and visual concept.

- **Q5:** generated a 29.5KB replacement. Headless browser validation observed advancing elapsed time and changing pressure/gas telemetry; it is a genuine working two-pass repair.
- **Q8:** generated a 30.7KB replacement but functional validation remained frozen.
- **Q6:** first repair produced 365 bytes. A fully isolated retry with the identical brief and a verified model registration again produced 365 bytes. It is treated as reproducible behavior, not an invocation mistake.

The preserved live artifacts are intentionally still available for human inspection. The working Q5 repair is served at `http://100.106.201.33:18997/volcano.html` while its host bridge remains running.

## Context ladder: selected Q5

The extended ladder was run only for Q5, as planned.

- **128K server context:** retrieval request used 111,038 prompt tokens and returned the distributed sentinels exactly as `amber|violet`. End-to-end wall time was 723.954 seconds (12m 4s).
- **196K server context:** a roughly 181K-token request ended in HTTP 500 after server allocation/processing. No completion artifact exists.
- **262,144:** not run. The 196K failure met the explicit stop criterion; spending more time to prove a theoretical maximum would not establish an operational route.

This establishes a measured successful 111K-token request, not a claim that Q5 provides practical 128K coding context. Its prefill wall time is already operationally expensive and the next rung failed.

## Fresh substitution task

The same independent `PolicyStore.rename_rule` task was materialized in four isolated fixtures. Acceptance required normalized names, an atomic collision failure, metadata preservation, a minimal patch, and passing tests. No model received peer output.

- **Local Q5:** the local tool-agent run terminated at its turn cap after 30.902 seconds, with 16 turns, 16 tool calls, and zero writes. It reported an apparent visible test success, but that test had the same worktree/path defect. Independent direct validation from the fixture (`PYTHONPATH=. python3 -m pytest -q`) failed both tests and confirmed no patch. This is a valid local failure, with a harness false-positive explicitly separated from the result.
- **Terra:** made the minimal `pop`/collision-check patch and passed the two tests both during the agent run and under an independent direct rerun. It consumed 34,793 reported tokens. The interactive wall interval was about 40 seconds.
- **GLM-5.3:** the first invocation was invalid because it used a generic Claude process without the Floor-managed Z.ai route. The corrected invocation used the managed Z.ai Anthropic-compatible endpoint and the `.claude-glm` profile. Live `c-translator` and `c-daily-ops` currently export `glm-5.2` as their controller default, but the same authenticated endpoint accepted `glm-5.3`. GLM-5.3 made a minimal patch and passed the two supplied tests under both its own run and independent direct validation. Its patch rejects a normalized same-name rename as a collision; that behavior is not covered by the task's acceptance tests and is less permissive than Terra's no-op handling.
- **Kimi K3:** the first invocation used the default Kimi home, whose model registry does not include `kimi-k3`. The managed `floor-design-adv` profile declares `kimi-code/k3-256k`; a non-mutating health prompt completed successfully on that route. The initial result was therefore invalid as a coding-agent score; the corrected executor-profile rerun is recorded below.

This comparison is deliberately incomplete rather than artificially ranked. It supplies two valid remote task results (Terra and GLM-5.3), one valid local failure (Q5), and the corrected Kimi executor result below. It does not supply comparable provider cost data.

## Corrected GLM-5.3 and Kimi K3 full-core rerun

The prior generic-provider calls were invalid and have been superseded by this direct, bounded rerun. GLM-5.3 used the authenticated Z.ai Anthropic-compatible route with a fixture-only tool allowlist. K3 used a disposable copy of the managed K3 profile at `/tmp/kimi-k3-executor-profile`; the original managed profile was not modified. Both ran only against fresh isolated fixtures.

| Contract | GLM-5.3 | Kimi K3 (`kimi-code/k3-256k`) |
| --- | --- | --- |
| Restricted Python canary (3 independent runs) | 3/3 direct passes | 3/3 direct passes |
| Fresh `TagIndex.rename` agentic task | Minimal patch created; independent visible+hidden acceptance: 3/3 passed. The model's own pytest calls remained approval-gated. | Minimal patch created, supplied test run completed, and independent visible+hidden acceptance: 3/3 passed. |
| Volcano one-shot | 55.8 KB HTML artifact; live browser telemetry advances and controls change state. | 30.1 KB HTML artifact; live browser telemetry advances; trigger-eruption control reached cooling/refilling state. |
| DOOM/raycaster one-shot | No artifact. The direct call reached its ten-minute bound. | No artifact. The direct call reached its ten-minute bound. |

Browser validation found no application exception in either volcano page. The sole console error in each case was a missing local `favicon.ico` (HTTP 404). GLM advanced from 92 to 94 MPa and 1 to 6 cm uplift during a three-second observation; later validation observed fracturing, dike ascent, phreatic-burst, wildfire, and controls changing the active composition/rate. K3 advanced from 28.7 to 31.7 MPa in the same observation window; its trigger-eruption control subsequently drove pressure down to 27.8 MPa, magma remaining to 16%, and rock integrity to 19% in the cooling/refilling state.

The two generated volcanoes are intentionally left available for human inspection at `http://100.106.201.33:19011/volcano.html` (GLM-5.3) and `http://100.106.201.33:19012/volcano.html` (K3). Their preview servers must remain running until Charles ends the inspection.

## Important limitations and next controlled action

The Q5 browser repair and 111K retrieval success justify retaining the route for further controlled work. They do not override the fresh agentic failure. Before considering a default-local coding promotion, rerun the fresh repository task with the test-execution path fixed in the agent harness and require repeated direct acceptance passes. The corrected K3 executor profile demonstrates that K3 can complete this bounded agentic task, but it does not establish a broad K3 coding ranking. Both remote browser calls failed to complete the raycaster artifact within the identical ten-minute bound, while their volcano artifacts were functional; that qualitative split should be preserved rather than collapsed into a single browser score.

No active Floor code, policy, launcher, or runtime behavior was modified by this experiment. All model work occurred in disposable fixtures or the isolated GMKtec experiment root.
