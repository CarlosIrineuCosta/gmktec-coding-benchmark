# Supervised Qwen 3.8 local-gallery comparison

Run date: 2026-09-02. This is a qualitative, supervised local-development
comparison, not a general coding leaderboard.

## Scope and method

Each candidate received the same unchanged local-only gallery task in a
disposable worktree. The task required retaining twelve supplied public-domain
images, researching and adding exactly twelve more compliant Met Open Access
or Library of Congress images, local asset storage and metadata, responsive
gallery UI, filters, and an accessible lightbox. The completed worktrees are
preserved under `demos/working/`.

The server was local `llama.cpp` build 10687, commit `92b19177a`, with all
layers offloaded to the AMD GPU. Each run used a 131072-token context,
`reasoning=on`, `reasoning-effort=xhigh`, reasoning preservation, temperature
1.0, top-p 0.95, top-k 20, min-p 0, presence penalty 0, and repetition penalty
1. No request carried a completion-token cap; the transport timeout was
unlimited. The bounded acquisition tool was the supplied
`python3 tools/met_open_access.py`; allowed build commands were `npm run build`
and `npm run test:e2e`.

Independent supervision could restate an existing criterion or correct an
observed acceptance failure, but did not change `TASK.md`, tests, assets, or
the required product. Raw interaction streams are not published because they
may contain full model interaction content. Reviewed screenshots are in
`evidence/2026-09-02-qwen38-gallery-comparison/`.

## Candidates and terminal classifications

| Candidate | Exact artifact | Terminal classification | Verified result |
| --- | --- | --- | --- |
| Qwen3.8-27B UD-Q6_K_XL | `Qwen3.8-27B-UD-Q6_K_XL.gguf`; `unsloth/Qwen3.8-27B-GGUF` revision `27af057ecb382ddfea5d12837360a8980560e3ed`; SHA-256 `701d8fa9ed214ab21bfc130cd2a7df19ca89bbef7713e2dfb19f3c63696aa917` | Accepted at 04:03:43 UTC | Build passed; independent browser check passed. |
| Qwen3.8-Flash-Next UD-Q3_K_XL | three `Qwen3.8-Flash-Next-UD-Q3_K_XL-0000N-of-00003.gguf` shards; `unsloth/Qwen3.8-Flash-Next-GGUF` revision `c8b5954a88c2775c546b92593eda40ea041d3176`; hashes in its demo notes | Accepted at 06:00:36 UTC | Build passed; independent browser check passed. |

The Q6 run had three earlier invalidated harness configurations before the
valid no-cap, unlimited-timeout run. Those attempts produced no candidate
output and are not a model score.

## Final comparison result

The Owner reviewed the completed Qwen galleries and rated both results as
perfect for this task. Both were visually good. The Owner ranked Flash as the
more polished result. The Owner expects additional instructions would bring
the Q6 result to the same polish level.

The earlier GLM 5.3 gallery was also visually checked by the Owner and
confirmed to run well. Its generated source was not retained after the
disposable run, so this is a qualitative Owner confirmation only. It is not a
repeatable retained-source result. The Owner considers the local Qwen3.8-27B
result to be at the same level as that GLM result.

| Candidate | Final task result | Visual assessment | Supervised controller elapsed time |
| --- | --- | --- | --- |
| GLM 5.3 | Owner-confirmed working gallery | Ran well | Not available; its disposable source and controller evidence were not retained. |
| Qwen3.8-27B UD-Q6_K_XL | Perfect result for this task; accepted | Visually good; same level as the GLM gallery in the Owner assessment | `02:15:21.929` |
| Qwen3.8-Flash-Next UD-Q3_K_XL | Perfect result for this task; accepted | Visually good; Owner-ranked as more polished | `01:53:46.803` |

The elapsed time starts when the durable controller created each valid Qwen
run. It ends at the accepted terminal classification. It includes model turns,
bounded tool use, required supervision, and validation work.

## Browser acceptance evidence

For both finished applications, independent browser validation confirmed:

- 24 local artworks render, including twelve added Met CC0 records.
- Category controls render and change the item count.
- The lightbox opens; Escape closes it and returns focus to the triggering
  image.
- A fresh browser session has no console errors.

The Q6 production build passed. Its fixture E2E command exited because
Playwright found no tests, not because an application assertion failed. The
Flash production build passed, but the model omitted the final E2E invocation
after its last successful build. These are distinct evidence limitations.

The final task rating above is based on the passing production builds and the
independent browser acceptance checks. It does not convert either E2E
limitation into a passing candidate E2E test.

## Observed supervision and operational behavior

The task deliberately allowed local research only through bounded sources. In
the xhigh baseline, both models nevertheless remained in a prolonged
research-only phase:

- Q6 completed 12 research turns and 40 search calls before an Owner-directed
  transition to the unchanged acquisition and development work.
- Flash completed 10 research turns and 20 search calls before the same
  transition.

This is useful operational-routing evidence, not a negative result. It shows
that a capable local coding model may need an explicit research-to-development
handoff for a bounded implementation task. It does **not** justify lowering
reasoning by default or modifying the task. A separate, controlled test can
compare lower reasoning effort or an external/specialized search worker.

After implementation, Q6 needed two browser-observed corrective passes: one
for initial lightbox/favicon behavior and one to render already-constructed
category buttons. Flash needed a validator correction so supplied legacy
records remained valid while added-record metadata stayed strict, plus the
missing local module entry point. These were corrections to existing
requirements, not scope expansion.

## Retained outputs

- [Q6 gallery source](../../demos/working/2026-09-02-qwen38-27b-q6-gallery/)
- [Flash gallery source](../../demos/working/2026-09-02-qwen38-flash-q3-gallery/)
- [Reviewed browser evidence](../../evidence/2026-09-02-qwen38-gallery-comparison/)

The Q6 and Flash previews remain separate, live local demonstrations. The
previous GLM preview process was absent from port 4185 during the final audit;
it was not replaced with a differently attributed site. Recovering that
specific preview requires its preserved GLM worktree or an explicit decision to
recreate it.
