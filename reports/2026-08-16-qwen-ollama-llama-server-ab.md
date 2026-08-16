# Qwen3-Coder 30B local backend A/B: first controlled evidence

**Date:** 2026-08-16

**Status:** completed local canary; useful serving-path evidence, not a model
quality ranking.

## Fixed inputs

- Model: `qwen3-coder:30b`.
- Canonical payload: existing Ollama GGUF blob
  `1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a`.
- Blob size: 18,556,688,736 bytes.
- llama.cpp: build 10454, commit
  `4df29be4f4c3673f428170fda944a5b19f743bb8`, Vulkan/RADV.
- Temperature: 0; generation cap: 1,024; streaming OpenAI-compatible chat.
- Task: isolated two-file Python correction. One generic tool function was
  offered; each assistant turn could make exactly one call. The executor
  rejected multiple, malformed, or disallowed calls and withdrew tools after a
  passing test before requesting the final response.
- Both endpoints ran on GMKtec loopback and never concurrently:
  - Ollama: `127.0.0.1:11434/v1`
  - llama-server: `127.0.0.1:8081/v1`

No driver, kernel, Ollama configuration, model file, or Floor route was changed
for this experiment.

## Valid results

Every valid repetition completed the correction and passed the test. Every run
used exactly four valid tool calls: two reads, one write, one test. There were
no duplicate or malformed tool calls.

| Backend | Requested/effective context | Repetitions | Test result | Mean request wall time | Mean first-token latency | Model load time |
|---|---:|---:|---|---:|---:|---:|
| llama-server | 8K / 8K | 3 | 3/3 passed | 3.198 s | 78.417 ms | 3.004 s |
| llama-server | 16K / 16K | 3 | 3/3 passed | 3.198 s | 78.096 ms | 3.004 s |
| llama-server | 32K / 32K | 3 | 3/3 passed | 3.210 s | 78.472 ms | 3.004 s |
| Ollama | 8K / 64K | 3 | 3/3 passed | 5.523 s | 254.067 ms | 3.125 s |
| Ollama | 16K / 64K | 3 | 3/3 passed | 5.554 s | 257.578 ms | 3.384 s |
| Ollama | 32K / 64K | 3 | 3/3 passed | 5.564 s | 257.618 ms | 3.609 s |
| llama-server | 64K / 64K | 3 | 3/3 passed | 3.197 s | 76.878 ms | 3.003 s |
| Ollama | 64K / 64K | 3 | 3/3 passed | 4.251 s | 194.492 ms | 3.859 s |

The matched 64K control is the only equal-context performance comparison. For
this narrow task, llama-server had approximately 1.33x lower request wall time
and 2.53x lower first-token latency than Ollama. That is backend-path evidence,
not a claim of better model reasoning.

## Context finding

Ollama reported `context_length: 65536` for every request. Its systemd
environment contains `OLLAMA_CONTEXT_LENGTH=65536`; this overrode or otherwise
prevented the requested 8K/16K/32K reduction. llama-server's `/props` recorded
the requested 8K, 16K, 32K, and 64K values exactly.

The 8K/16K/32K Ollama rows must therefore not be used for equal-context speed
comparison. They remain useful evidence that the exact same model/tool contract
works through both backends. The service override was observed but not changed.

## Invalid attempts retained

Two earlier 8K attempt sets were preserved and excluded from the table:

1. `invalid-missing-pytest-20260816`: GMKtec lacked pytest. The test command
   was not executable, so the results were infrastructure-invalid.
2. `invalid-harness-tools-offered-after-pass-20260816`: the initial strict
   executor continued offering a tool after a passing test. Qwen made the
   correction correctly but kept selecting an offered call; the executor was
   corrected to withdraw tools before requesting the final completion.

Neither invalid set was rerun as a model retry. The final labeled run used the
corrected environment and contract.

## Interpretation and next step

`llama-server` has now demonstrated a stable, observable local tool-serving
path for Qwen3-Coder 30B at 8K through 64K. Its `/props` and `/metrics` expose
effective context and performance data that the current Ollama route did not
make equally controllable in this experiment.

The chat template remains a bounded caveat: llama-server used the template
embedded in the same GGUF via Jinja, while Ollama reported its `qwen3-coder`
renderer/parser. The common tool behavior was identical for this canary, but
byte-identical rendered prompts were not proven. Before using this result for
larger coding tasks, add a template-rendering capture to the runner and use the
same frozen task packet.

Raw private records are retained on GMKtec under `/home/cdc/llm/ab/results/`
and locally under the ignored `results/local-ab/` directory.
