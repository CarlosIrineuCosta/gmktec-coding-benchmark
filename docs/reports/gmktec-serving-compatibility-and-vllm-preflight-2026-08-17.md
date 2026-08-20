# GMKtec Serving Compatibility and vLLM Preflight

**Date:** 2026-08-17
**Status:** minimal compatibility pass complete; Docker installed; isolated
vLLM/ROCm OpenAI-compatible smoke passed

## Controlled Qwen llama-server baseline

The existing controlled path was re-run at 8K with the exact prior GGUF and
llama.cpp build:

- artifact: Qwen3-Coder 30B Q4_K_M, GGUF SHA-256
  `1194192cf2a187…8863006a`;
- server: llama.cpp build 10454, commit `4df29be4f`, Vulkan/RADV;
- observed server context: 8,192; embedded Jinja template and tool parser
  exposed through the OpenAI-compatible endpoint;
- result: the model returned `READY`, then emitted ten valid sequential
  `repository_action` tool calls. Raw SSE/parser evidence is retained in
  `/home/cdc/llm/ab/results/baseline-audit-venv-20260817/`.

The end-to-end fixture did not terminalize because the existing canary hard
codes `/usr/bin/python3 -m pytest`, while that interpreter lacks pytest. The
model had already made the expected read/read/write/run-test sequence and then
repeated the test call after receiving the harness error. This is an executor
environment defect, not evidence that Qwen3-Coder or llama-server lacks tool
support. No canary source was changed.

## Isolated Ollama plain-completion probes

All probes used one temporary loopback-only daemon at a time, 8K requested
server context, the fixed deterministic prompt, and verified cleanup.

| Model | Plain and chat result | Context observation | Qualification state |
| --- | --- | --- | --- |
| Qwen3-Coder Next | exact fixed reply from native generate and chat | 8K | basic serving contract passes on current Ollama; former older-llama.cpp load failure is not a model-quality result |
| TranslateGemma 12B | exact fixed reply from native generate and chat | 8K | basic serving contract passes; translation quality remains unqualified |
| GPT-OSS 120B | chat passes with `thinking` separated from final content when given 256 output tokens | 8K | explicit reasoning/output budget is required; the earlier empty content at 16/64 tokens was not a parser failure |
| GLM-4.6V-Flash 9B | exact fixed reply from native generate and chat | **4K**, despite 8K daemon configuration | basic chat contract passes; the source of the 4K cap is now classified below |

These are compatibility observations only.

### Sequential tool-contract probes

Using a separate loopback-only daemon and one `echo_status` function contract,
both Qwen3-Coder Next and GPT-OSS made exactly one correctly named tool call
with `{"status":"ready"}`, accepted the tool result, and returned a final natural
language answer. Their observed allocations were 8K. This clears only the
minimal serving/tool contract; it does not score complex coding or agentic
quality.

### GLM 4K context source

The 4K observation was diagnosed by inspecting layers rather than changing
flags until it disappeared:

- the GLM GGUF reports native `glm4.context_length = 131072`;
- the temporary Ollama daemon was configured with an 8,192-token server
  default and the probe client sent no `num_ctx` override;
- `POST /api/show` for the installed package reports
  `PARAMETER num_ctx 4096`;
- the chat template only formats the prompt, llama-server is not in this
  Ollama path, and no backend-specific cap was observed.

Therefore the current 4,096 allocation is imposed by the installed Ollama
model package's parameter layer. It is not evidence of a 4K-native GGUF or a
GLM model limitation. Any later precedence test must explicitly distinguish a
package parameter from a request override.

One explicit precedence confirmation then used an 8K daemon and an 8K
`options.num_ctx` request against that same package. `/api/ps` observed 8K and
the fixed response completed. Thus the package establishes GLM's default, but
the native request layer can override it in an isolated fresh daemon. The
stable production-like service was not involved.

## Disposable Ollama helper

The tested reusable helper now lives at:

```text
/home/cdc/llm/ab/ollama-bench
```

It accepts `ollama-bench <server-context> [request-context]`, starts a
loopback-only daemon on 11435, writes raw request/response/allocation evidence
under `/home/cdc/llm/ab/ollama-bench-runs/`, and verifies daemon/port cleanup.
Its first self-test observed an 8K allocation and recorded `cleanup=ok`.

## vLLM/ROCm preflight and installation

Before installation, GMKtec had `/dev/kfd`, `/dev/dri/renderD128`, Vulkan/RADV,
and ample storage, but no container runtime or ROCm host Python tools. Docker
Engine was therefore installed through Docker's official Ubuntu repository,
then verified through `hello-world`.

Current verified Docker state:

- Docker Engine/client 29.7.2;
- `cdc` is in the `docker`, `video`, `render`, and `ollama` groups;
- storage driver: overlayfs; 1.5 TB remained free before the vLLM image pull;
- official image selected: `vllm/vllm-openai-rocm:latest`.

No vLLM, PyTorch, ROCm Python, or TheRock package was installed into the host
Python environment.

## vLLM/ROCm smoke result

The official image completed with immutable identity:

```text
vllm/vllm-openai-rocm@sha256:bb44b39aea26798cce43030a98bf48efd0322ca7147367db86e38b96bd80f0e7
```

It ran vLLM 0.27.1 in a disposable Docker container with `/dev/kfd`,
`/dev/dri`, `video`, shared IPC, a dedicated Hugging Face cache, and the sole
published port `127.0.0.1:8000`. The public Qwen/Qwen3-0.6B smoke artifact was
downloaded only into that dedicated cache.

The container log proves that vLLM:

- resolved `Qwen3ForCausalLM`;
- initialized its ROCm engine against the Radeon 8060S/RADV device;
- loaded 1.40 GiB of weights and created a 27.81 GiB KV cache at 8K context;
- selected a Triton attention fallback after its ROCm custom paged-attention
  kernel was unavailable;
- exposed the OpenAI-compatible `/v1/models` endpoint with an 8,192-token
  model limit.

Both `/v1/completions` and `/v1/chat/completions` returned valid structured
responses. With `max_tokens:16`, Qwen3's default reasoning text consumed the
budget before it reached the requested literal answer, yielding
`finish_reason:length`. This proves a serving/template/token-budget contract
that needs explicit control in later Qwen3 quality tests; it is not a vLLM
startup failure.

The container was stopped and removed after the smoke. Port 8000 is no longer
listening. Non-secret responses, model metadata, and container logs are stored
under:

```text
/home/cdc/llm/ab/results/vllm-rocm-smoke-20260817/
```

## vLLM ROCm concurrency functionality smoke

A second fresh, disposable container used the same immutable image, the public
`Qwen/Qwen3-0.6B` model, an 8,192-token limit, and one fixed bounded
completion workload (736 prompt tokens and 48 generated tokens per request).
It tested simultaneous request counts of 1, 2, 4, and 8.

| Concurrent requests | Aggregate completion tok/s | TTFT range | Errors |
| ---: | ---: | ---: | ---: |
| 1 | 94.01 | 92.91 ms | 0 |
| 2 | 202.91 | 29.42–55.12 ms | 0 |
| 4 | 394.23 | 28.67–60.61 ms | 0 |
| 8 | 444.18 | 29.22–94.97 ms | 0 |

The runner also records a clearly labelled **prefill proxy**, computed from
client-observed wall time and prompt-token counts; it is not a server-reported
prefill throughput metric. Per-request decode durations and raw usage/TTFT are
retained with the run. At the end of the workload, `docker stats` recorded
6.066 GiB container memory, 274 PIDs, and no errors. Server logs record a
260,368-token GPU KV cache and a Triton fallback because the ROCm custom paged
attention kernel was unavailable.

This is a functionality/concurrency smoke only. It proves that the isolated
OpenAI-compatible ROCm route accepted and completed 1/2/4/8 concurrent
bounded requests; it does not rank vLLM against llama-server or establish a
production performance result. The container was stopped/removed, port 8000
was free, and the stable Ollama service remained active.

Evidence is retained under:

```text
/home/cdc/llm/ab/results/vllm-rocm-concurrency-20260817/
```

## Exact Qwen3-Coder HF-format vLLM smoke

The exact upstream counterpart of the controlled 18.56 GB Q4 GGUF baseline
was downloaded as the pinned BF16 safetensors snapshot
`Qwen/Qwen3-Coder-30B-A3B-Instruct@b2cff646eb4bb1d68355c01b18ae02e7cf42d120`.
The snapshot has 16 shards and 61,079,826,794 bytes. It was mounted
read-only from the dedicated cache into a fresh loopback-only ROCm container.

vLLM 0.27.1 resolved `Qwen3MoeForCausalLM`, loaded the checkpoint at an
explicit 8,192-token limit, and exposed the selected served name through
`/v1/models`. Both a deterministic completion and deterministic chat request
returned the requested literal responses with `finish_reason: stop`.

Engine evidence records 62.18 GiB consumed for model loading, a 64,800-token
GPU KV cache (about 7.91 simultaneous 8K requests), and the expected
ROCm/Triton route. The endpoint was intentionally stopped and removed after
capture; port 8000 was free and the stable Ollama service was still active.

Three early launcher attempts failed before model loading because the image's
default entrypoint already includes `vllm serve`; a later snapshot-only mount
also failed because Hugging Face snapshot files are relative symlinks to the
cache's `blobs/` directory. Retained logs classify these as launcher/cache-mount
defects, not model, weight, ROCm, or quality failures. The successful attempt
mounted the whole dedicated cache read-only.

Docker's own RSS snapshot was 27.42 GiB while the engine's accelerator-memory
accounting reported 77.52 GiB consumed (weights plus non-torch), so the latter
is the relevant allocation evidence for this APU route. These are startup and
compatibility observations only, not a matched performance comparison with the
quantized llama.cpp baseline.

Evidence is retained under:

```text
/home/cdc/llm/ab/results/vllm-rocm-qwen3-coder-30b-smoke-20260817/
```

## Next actions

1. Design the first matched workload comparison while keeping the GGUF Q4 and
   HF BF16 format difference explicit; start with the actual target concurrency
   shape rather than a single-user winner claim.
2. Compare vLLM only in prompt-heavy or concurrent workload shapes, not against
   the single-user llama-server coding baseline.
3. Return to model-specific quality qualification only after the serving
   contract for each model is valid.
