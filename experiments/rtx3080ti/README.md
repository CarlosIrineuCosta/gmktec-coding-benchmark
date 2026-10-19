# RTX 30-series Windows probe versus GMKtec

Two goals: find the smallest Qwen3.5 artifact that serves a real coding
workload with decent output on the card currently attached to the Win11
machine, and keep a matched GMKtec control so any later hardware decision
compares like with like. This is a serving and coding-review probe, not the
full Floor benchmark. It reuses the local OpenAI-compatible interface and
keeps all generated responses in private JSON files on the operator's
machine. Step-by-step instructions for the Win11 operator agent (Codex) live
in [win11-runbook.md](win11-runbook.md); this file records the plan and the
decisions behind it.

## Machine state (2026-10-19)

The Win11 system currently has the **RTX 3070 Ti (8 GB)** attached. The
3080 Ti (12 GB) is available as a board swap; a 3090 (24 GB) is a
conditional tier only if earlier results justify it. Never compare speeds
across different model artifacts and attribute the difference to hardware.

## HyperQwen verdict (checked 2026-10-19)

[syv-ai/HyperQwen](https://github.com/syv-ai/HyperQwen) is a vLLM 0.31 patch
series plus a model-preparation pipeline that serves **exactly one
checkpoint, Qwen3.8-27B** (requantized heads, calibrated draft vocabulary,
DFlash2/MTP speculative decoding, OpenAI-compatible API on :18020, Docker
first). Concretely checked:

- The README names no other model; smaller checkpoints for 16/12 GB cards
  are roadmap items, not built artifacts.
- None of the 213 pull requests (5 open) adds a smaller checkpoint or any
  Qwen3.5 support; recent work is KV-cache kernels and vLLM porting.
- Reference hardware is one 24 GB card (RTX 3090, sm86). The lowest working
  multi-GPU datapoints are 2x 12 GB RTX 3060 at TP=2 (#68, 24 GB total) and
  2x 16 GB RTX 5070 Ti at TP=2 (#342, 32 GB total).

Consequences per card option:

| Card(s) | VRAM | HyperQwen? |
| --- | --- | --- |
| 3070 Ti | 8 GB | No. Model is ~20 GB after requantization. |
| 3080 Ti | 12 GB | No. |
| 3080 Ti + 3070 Ti (TP=2) | 20 GB | No first test. Below the documented 24 GB floor, with unequal per-card memory. At most a later bounded experiment if Charles asks. |
| 3090 | 24 GB | Yes - this is the reference configuration, and the only tier where HyperQwen testing starts (Docker Desktop + WSL2). |

So "test a smaller Qwen3.5 model inside HyperQwen" is not possible today.
Small-model testing happens through **llama.cpp CUDA**, which is this
experiment's serving plane and already the GMKtec stack's plane. HyperQwen
remains the 3090-tier question, and it does not gate this experiment.

## Test ladder (llama.cpp CUDA, text-only, `--no-mmproj`)

| Tier | Card(s) | Runs |
| --- | --- | --- |
| 0 - now | 3070 Ti (8 GB) | 4B Q6_K (3.53 GB) at 8K - primary; 4B Q8_0 (4.48 GB) at 8K - quality point; 9B Q4_K_M (5.68 GB) at 4K - stretch, OOM allowed and recorded as data |
| 1 - board swap | 3080 Ti (12 GB) | 9B Q4_K_M at 8K; 9B Q6_K (7.46 GB) at 8K |
| 2 - both boards | 12 + 8 = 20 GB | Optional llama.cpp row-split exploration only; HyperQwen still no |
| 3 - conditional | 3090 (24 GB) | HyperQwen Qwen3.8-27B reference test (Docker Desktop + WSL2) |

Model artifacts: [unsloth/Qwen3.5-4B-GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF)
and [unsloth/Qwen3.5-9B-GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF),
Apache-2.0. Both repos also ship mmproj files (these are vision-language
models); this experiment serves text only and passes `--no-mmproj`.

## Probe

`endpoint_probe.py` (Python standard library only) performs one warmup and
three recorded runs of a short code-review prompt and a repetitive copy
prompt per invocation, storing model output, token usage if served,
first-token latency, wall time, and `nvidia-smi` snapshots in one JSON file.
A real, sanitized task prompt can be added via `--prompt-file`. Do not use a
hidden answer or a canonical Floor checkout as candidate work material.
Neither case automatically scores code-review correctness.

### Quality gate for "decent output"

Read the outputs and record a verdict per run:

- Coding case: the model flags at least one of the two seeded defects in the
  included `claim`/`deliver` source (a stale claim returned after the lease
  expires; a send-then-record window that can replay an event) and proposes
  a concrete fix. Naming zero real defects is a fail regardless of fluency.
- Copy case: the passage is reproduced exactly, no preface.
- Neither case may end with `finish_reason` `length` truncation.

### GMKtec control (later, separate from the Win11 runbook)

Use the existing `cdc` Unsloth/llama.cpp stack to launch a disposable local
server for the **same GGUF** and the same context, on an unused loopback
port, and run this same script against its `/v1` endpoint. Capture exact
model file hash, llama.cpp build, Vulkan/RADV version, host power mode, and
launch command. If driving it from the Windows machine, reach the endpoint
through an SSH tunnel; do not rebind any server to the LAN for a test.
The first-token value includes queueing and prompt processing; the decode
rate divides reported completion tokens by time since the first visible
token, and reasoning tokens may not appear as visible text. Compare wall
time and reported usage first, then inspect outputs. Run the repository's
accepted, isolated gallery and review tasks only after the endpoint and a
tool-call canary work on the new server/model pair.

## Results

Raw JSON stays private on the operator's machine. The only artifact that
comes back to this repository is the sanitized summary table produced at
the end of the runbook (timings, VRAM, pass/fail on the quality gate, and
short notes) plus, if the operator chooses, excerpts of model output with
no private material.
