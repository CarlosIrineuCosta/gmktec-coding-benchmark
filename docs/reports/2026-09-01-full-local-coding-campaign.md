# Full local coding campaign — 2026-09-01

## Scope and evidence boundary

This report summarizes the 18-cell local coding campaign. Each candidate received a fresh held-out code-review workspace and a fresh photo-gallery workspace. Raw conversations, tool outputs, private fixtures, gold data, and screenshots remain on the GMKtec private evidence volume and are not included here.

The controller recorded every cell as terminal before this report was written: 18 terminal, zero active, zero pending.

## Common configuration

- Harness: restartable supervised OpenAI-compatible local harness, with one model turn per explicit coordinator action.
- Sampling: temperature 1.0, top-p 0.95, top-k 20, min-p 0, maximum completion 8,192 tokens.
- Server: disposable loopback-only llama-server instances; persistent Studio was not restarted.
- Tasks: held-out three-defect code review; local 12-image responsive gallery with build/browser acceptance.
- Intervention policy: substantive implementation assistance was prohibited. Gallery cells could receive bounded diagnostic/criterion reminders only.

## Results

| Candidate | Review | Gallery | Operational observation |
| --- | --- | --- | --- |
| Qwen 3.8 27B Q6 | accepted, 3/3 credited | accepted | Strongest complete local coding result in this campaign. |
| Qwen 3.8 Flash Next Q3 | accepted, 2/3 credited | accepted | Completed both tasks. |
| Qwen 3.5 9B Q6 | accepted, 2/3 credited | accepted with defects | Gallery had 13 images rather than the required 12. |
| Nemotron 3 Nano 4B Q8 | task not completed, 0/3 | task not completed | Empty review; malformed/non-executed gallery behavior. |
| Gemma 4 31B Q6 | accepted, 2/3 credited | task not completed | Gallery context exhaustion after partial work. |
| Nemotron 3.5 Lightning Q8 | accepted, 2/3 credited | task not completed | Partial gallery; context exhaustion before independent acceptance. |
| Nemotron Super v1 Q6 | task not completed, 0/3 | task not completed | Qualified Pythonic adapter worked, but review was a placeholder and gallery remained partial after I2. |
| Nemotron Super v1.5 Q6 | task not completed, 0/3 | task not completed | Qualified JSON adapter served, but review hallucinated an uninspected path; gallery made only placeholder writes after I2. |
| ASearcher Web QwQ Q5 | accepted, 0/3 credited | task not completed | Tool-active review with non-gold findings; partial gallery failed browser validation. |

## Interpretation

The campaign is evidence of task routing, not a single leaderboard. Qwen 3.8 27B is the clear one-shot coding choice here. Flash Next is a viable lower-footprint alternative. Qwen 3.5 produced a usable gallery but missed a concrete image-count requirement. The remaining candidates show meaningful failure modes—hallucinated review targets, tool-format dependence, extremely long planning generations, partial file production, and context exhaustion—that should be retained rather than normalized away.

## Artifact index

- Private durable evidence root: GMKtec local private results volume, campaign `full-local-coding-campaign-20260901`.
- Public sanitized summary: `community/artifacts/local-model-evaluation/2026-09-01-summary.json`.
- Public runner source: `benchmark/supervised_eval/`.

