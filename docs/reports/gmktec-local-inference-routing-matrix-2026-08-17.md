# GMKtec Local-Inference Preliminary Routing Matrix

**Date:** 2026-08-17
**Status:** Gates 0–6 executed under Charles's one-off lab authorization;
preliminary routing synthesis awaiting Charles review

## Decision frame

This is a routing matrix, not a single-stack selection. A result is meaningful
only with its model artifact, server/engine, backend, context, and concurrency
shape. The stable 64K Ollama service was not changed during this work.

## Evidence-indexed routes

| Workload | Preliminary route | Measured basis | Confidence | Constraints |
| --- | --- | --- | --- | --- |
| Casual/private chat and simple local API use | Ollama, current Vulkan/RADV route | disposable 8K chat contracts passed for Qwen Next, TranslateGemma, GPT-OSS, and GLM | medium | convenience route; GPT-OSS needs an output budget that leaves room after reasoning |
| Coding / tools, one active agent | llama-server + controlled Qwen3-Coder Q4_K_M GGUF + Vulkan/RADV | 8K tool canary produced valid sequential actions; fixed coding run at one request delivered 40.94 aggregate completion tok/s, 1.62 s TTFT | medium-high | the legacy executor's system Python lacks pytest; that fixture defect is not model/tool failure |
| Coding / tools, four local clients | vLLM + pinned Qwen3-Coder BF16 + ROCm container | fixed coding run at four requests: 56.44 aggregate completion tok/s, 0.17–0.43 s TTFT, zero errors | medium | BF16 vLLM versus Q4 llama.cpp is a route result, not a pure backend winner claim |
| Prompt-heavy extraction / summarization, one request | llama-server + Q4 GGUF + Vulkan/RADV | 4,576-token extraction prompt: 22.02 aggregate completion tok/s, 4.13 s TTFT | medium | controlled one-request route; quality was not scored |
| Prompt-heavy extraction / summarization, four requests | vLLM + pinned BF16 + ROCm container | same fixed prompt/target at four requests: 51.70 aggregate completion tok/s, 0.25–0.99 s TTFT, zero errors | medium | strongest measured concurrent prompt-heavy route; retain BF16/Q4 caveat |
| Translation | Ollama + TranslateGemma 12B + Vulkan/RADV | independent 1,950-token English-to-Brazilian-Portuguese workload at observed 8K; native Ollama metrics show about 750 prompt tok/s and 25 decode tok/s | low-medium | 256-token bounded run ended by length; it establishes serving/performance shape, not translation-quality acceptance |
| GLM use | Ollama only after explicit package-context handling | native GGUF reports 131K; installed package defaults to `num_ctx 4096`, while an explicit fresh-daemon 8K request observed 8K | low | 4K cap is package configuration, not a native-model/backend limit |

## Fixed workload records

Both Qwen3-Coder benchmark families used an explicit 8K per-request context,
temperature zero, a 128-token target, OpenAI-compatible streaming completions,
and concurrency shapes 1 and 4. Raw output, token usage, per-request TTFT,
decode duration, server logs, and cleanup evidence are retained under:

```text
/home/cdc/llm/ab/results/matched-qwen3-coder-8k-20260817/
```

### Coding profile

The profile had a 6,407-character structured coding prompt (1,941 tokens per
request). At one request, llama-server/Q4/Vulkan completed at 40.94 aggregate
completion tok/s versus vLLM/BF16/ROCm at 16.17. At four requests, the figures
were 61.46 and 56.44 respectively. The vLLM run had much lower measured TTFT
at four concurrent requests (0.17–0.43 s versus 1.76–5.10 s).

### Extraction / summarization profile

The profile had a 15,709-character incident ledger (4,576 tokens per request)
and exact JSON extraction contract. At one request, llama-server/Q4/Vulkan
completed at 22.02 aggregate completion tok/s versus vLLM/BF16/ROCm at 13.32.
At four requests, vLLM/BF16/ROCm completed at 51.70 versus
llama-server/Q4/Vulkan at 30.40. Four-request TTFT was 0.25–0.99 s for vLLM
and 7.15–12.79 s for llama-server.

The client-computed prompt-token throughput fields are retained as **prefill
proxies**, not server-reported prefill benchmarks. Do not collapse them with
decode throughput into one global token/sec statement.

## Serving and operational findings

- vLLM 0.27.1 works in the isolated ROCm container on this Strix Halo host;
  the pinned image and 30B-A3B HF revision both passed model-list, completion,
  and chat compatibility.
- The vLLM engine used ROCm/Triton paths and reported an absent device-specific
  MoE configuration, so later tuning may improve its current result.
- The 30B BF16 checkpoint consumes substantially more accelerator memory than
  the Q4 GGUF. At 70% vLLM GPU-memory utilization it reported approximately
  62.18 GiB for model loading and a 64K–69K token KV cache, sufficient for the
  tested four-request 8K shape.
- Qwen Next and GPT-OSS passed the minimal native-Ollama sequential-tool
  contract. TranslateGemma's intended translation contract passed basic
  serving. The GLM context anomaly is classified at the package-parameter
  layer.

## What is not yet established

1. A same-artifact/same-quant Vulkan-versus-HIP comparison. The installed
   llama-server baseline is Q4 GGUF, while vLLM requires the upstream BF16
   checkpoint; the current numbers must not be represented as a pure backend
   shootout.
2. Translation quality or unconstrained translation completion.
3. Complex tool/coding quality comparison across servers.
4. A production auto-router, provider integration, stable-service change, or
   any Floor runtime change.

## Recommended next test, if further precision is needed

Run a dedicated long-prompt, short-answer extraction test at target concurrent
client counts using one exact artifact format where both engines can serve it.
That is the cleanest remaining way to sharpen the prompt-heavy routing boundary
without treating this preliminary matrix as a monoculture decision.
