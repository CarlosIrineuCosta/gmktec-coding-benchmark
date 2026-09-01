# C benchmark qualification — 2026-09-01

## Scope and reproducibility

This is the authorized qualification gate, not a larger-model ranking.  Public
runner/task code is on `agent/local-model-evaluation-pilot-20260830` at
`25e4926`; raw answers, transcripts, hidden scoring maps, telemetry samples,
and run state remain private on GMKtec.  Every disposable server bound only to
`127.0.0.1`, used local `llama-server` `0.3.0-dev build10687 92b19177a`, and
was stopped after its terminal result.

The common task was the public synthetic `routing-probe-2026-09-01`: return a
unified diff for `retry.py`; the independent standard-library acceptance test
requires normalized `timeout`/`rate_limited` status and fewer than three prior
attempts.  Task requests used temperature `1.0`, top-p `0.95`, top-k `20`,
min-p `0`, no presence/frequency penalty, maximum `4096` tokens, 16K context,
`--jinja`, and model-native `--reasoning auto --reasoning-effort default`.

## Browser and preserved Qwen review correction

Owner-authorized Chromium remediation installed the ordinary Playwright host
libraries through `npx playwright install-deps chromium`.  Chromium launched;
the canonical gallery acceptance test passed.  Deep revalidation found one
real artifact issue: at 390x844 the gallery lightbox close control was below
the viewport.  The prior failure is therefore not a valid negative model result,
but the gallery is not fully mobile-accepted.

The preserved private Qwen review was rescored at finding level: **5 reported,
3 credited, 2 non-gold, recall 1.00, precision 0.60**.  No review was rerun.
The Aug-30 public report received only this arithmetic correction.

## Installed public artifacts

| Role | Repository / revision | Selected or inventory-only artifact |
| --- | --- | --- |
| heavy_reasoning_coding | `unsloth/Qwen3.8-Flash-Next-GGUF` `c8b5954` | `UD-Q3_K_XL`, three shards: 10,946,624 + 49,983,253,824 + 39,992,153,376 bytes |
| heavy_reasoning_coding | `unsloth/Qwen3.8-27B-GGUF` `27af057` | `UD-Q6_K_XL`, 25,299,061,664 bytes; Q5 variant `4ca7207`, 20,876,938,144 bytes, inventory-only |
| medium_general | `unsloth/Qwen3.5-9B-GGUF` `3885219` | `UD-Q6_K_XL`, 8,756,929,760 bytes |
| heavy_reasoning_coding | `unsloth/gemma-4-31B-it-GGUF` `c1ac76e` | `UD-Q6_K_XL`, 27,521,338,304 bytes; Q8 and MTP artifacts inventory-only |
| heavy_reasoning_coding | `unsloth/Llama-3_3-Nemotron-Super-49B-v1-GGUF` `6c679d1` | `UD-Q6_K_XL`, 43,417,787,904 bytes |
| heavy_reasoning_coding | `unsloth/Llama-3_3-Nemotron-Super-49B-v1_5-GGUF` `cae8fb4` | `UD-Q6_K_XL`, 43,417,790,368 bytes |
| heavy_reasoning_coding | `unsloth/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF` `f2d3fe3` | `UD-Q8_K_XL`, 38,615,380,032 bytes |
| tiny_fast | `unsloth/NVIDIA-Nemotron-3-Nano-4B-GGUF` `8e81be5` | `UD-Q8_K_XL`, 5,626,063,008 bytes |
| specialized | `mradermacher/ASearcher-Web-QwQ-i1-GGUF` `8f6109f` | `i1-Q5_K_M`, 23,262,157,568 bytes |
| specialized | Aya 23 8B/35B, Tencent Hy-MT2 Q4/Q8, and bge-small | translation or embedding artifacts; inventory-only |

Cache-object SHA-256 identities and exact filenames are retained in the
private run specifications.  Inventory-only variants were not separately
qualified because they duplicate the same base model role.

## Gate and common-task evidence

All nine plausible coding/agent candidates passed serving and one bounded tool
action.  Qwen/Gemma used native OpenAI tools.  Super v1.5 used NVIDIA's
documented JSON tag adapter; Super v1 used its documented Python-call tag;
Lightning accepted its documented XML/Qwen3-Coder representation; the remaining
models accepted native OpenAI tools.  ASearcher had no network search enabled.

| Candidate | Gate A / Gate B | Common task | Task wall / TTFT | Peak RSS KiB |
| --- | --- | --- | ---:| ---:|
| Qwen 3.8 Flash Next Q3 | pass / pass | fail: non-diff output | 21.279s / 18,226ms | 28,610,180 |
| Qwen 3.8 27B Q6 | pass / pass | **pass**: patch + 3 tests | 142.437s / 133,168ms | 544,672 |
| Qwen 3.5 9B Q6 | pass / pass | fail: no status normalization | 27.994s / 25,066ms | 278,764 |
| Gemma 4 31B Q6 | pass / pass | fail: no status normalization | 35.480s / 24,992ms | 419,188 |
| Nemotron Super v1.5 Q6 | pass / pass | fail: trailing fence malformed diff | 156.893s / 124,894ms | 194,736 |
| Nemotron Super v1 Q6 | pass / pass | fail: trailing fence malformed diff | 63.804s / 2,237ms | 193,872 |
| Nemotron 3.5 Lightning Q8 | pass / pass | fail: no status normalization | 22.232s / 20,422ms | 288,780 |
| Nemotron 3 Nano Q8 | pass / pass | fail: non-diff output | 7.003s / 5,905ms | 350,736 |
| ASearcher Web QwQ Q5 | pass / pass | fail: code plus malformed placeholder diff | 40.816s / 28,521ms | 187,100 |

AMD DRM telemetry was available for every run.  It recorded VRAM-equivalent
and GTT peaks alongside system memory; model-visible token accounting includes
hidden reasoning for several models, so calculated decode rates are not used
as comparative quality claims.

## Recommendation and remaining blocker

Advance **Qwen 3.8 27B Q6** as the sole demonstrated heavy reasoning/coding
candidate for representative-task campaign design.  Keep the other passed-gate
models as compatible alternatives with the recorded output-format/task failures;
do not call them quality failures beyond this one task.  Translation and
embedding artifacts were not in scope.

There is no infrastructure blocker before GPT writes the final campaign task
file.  The concrete next instruction should define representative task families,
role coverage, acceptance criteria, and any deliberately different sampling
settings.  Approximate Codex supervisory usage for this qualification pass was
465k tokens at the final task-completion checkpoint.
