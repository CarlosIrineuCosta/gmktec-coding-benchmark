# GMKtec Qwen3-Coder HF Counterpart Provenance Record

**Date:** 2026-08-17  
**Status:** download complete; exact HF-format counterpart is available in the
isolated vLLM cache and has passed a narrow vLLM/ROCm API smoke

## Purpose

This record binds the planned vLLM model to the existing controlled
llama-server baseline. It does not claim that cross-format results will be
directly interchangeable: the baseline uses a quantized GGUF through
llama.cpp/Vulkan, whereas this counterpart uses upstream BF16 safetensors
through vLLM/ROCm.

## Controlled GGUF baseline

| Field | Value |
| --- | --- |
| Ollama tag / controlled artifact | `qwen3-coder:30b` |
| Path | `/usr/share/ollama/.ollama/models/blobs/sha256-1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a` |
| SHA-256 | `1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a` |
| Stored bytes | 18,556,688,736 (18.56 GB decimal) |
| GGUF architecture | `qwen3moe` |
| llama.cpp baseline | build 10454, commit `4df29be4f4c3673f428170fda944a5b19f743bb8` |

The GGUF's `qwen3moe` architecture, the local tag, and its embedded
Qwen3-Coder template identify the upstream family as
Qwen3-Coder-30B-A3B-Instruct. This is a family-and-architecture provenance
binding, not a claim that the 18.56 GB Q4 GGUF and BF16 checkpoint have
identical numeric weights.

## Selected HF counterpart

| Field | Value |
| --- | --- |
| Repository | `Qwen/Qwen3-Coder-30B-A3B-Instruct` |
| Revision (immutable commit) | `b2cff646eb4bb1d68355c01b18ae02e7cf42d120` |
| Architecture | `Qwen3MoeForCausalLM` / `qwen3_moe` |
| Upstream parameter representation | BF16, 30,532,122,624 parameters |
| Repository storage reported by HF | 61,066,575,656 bytes (61.07 GB decimal), including 16 safetensor shards and tokenizer/config assets |
| License | Apache-2.0 |
| Destination | `/home/cdc/llm/vllm-hf-cache` only; no host Python package installation and no production Ollama store mutation |

The selected repository and revision come from the publisher's Hugging Face
model API. The API lists 16 `model-*-of-00016.safetensors` shards and the
Qwen3-Coder tool-parser/template assets at this revision.

## Storage preflight

Before download, the GMKtec filesystem containing the cache had 1.5 TB
available (`/dev/nvme0n1p2`, 1.8 TB total, 253 GB used). The planned upstream
repository footprint was approximately 61.07 GB, leaving approximately 1.44 TB
before filesystem overhead. No deletion, movement, or modification of existing
models was required.

The selected Qwen3-Coder snapshot now records 61,079,826,794 bytes with zero
incomplete shards. The complete dedicated cache is 62,600,947,887 bytes because
it also retains the small-model smoke cache and HF metadata. After download,
1.4 TB remained free; no existing artifact was moved or deleted.

## Download guardrails

- download the revision pin only, into the dedicated vLLM Hugging Face cache;
- retain the resulting snapshot/commit evidence and actual post-download size;
- use the disposable ROCm container route; do not install vLLM, PyTorch, ROCm
  Python packages, or TheRock into the host Python environment;
- do not infer a llama.cpp-versus-vLLM winner from cross-format output alone;
  future matched tests must report the format/quant difference explicitly.

## Initial vLLM load result

The pinned snapshot passed a disposable loopback-only vLLM 0.27.1/ROCm smoke
at 8,192 context: vLLM resolved `Qwen3MoeForCausalLM`, loaded the 16 BF16
shards, and served valid OpenAI-compatible model-list, completion, and chat
responses. This confirms the selected HF counterpart is usable for later
matched workload work; it does not yet compare quality or performance with the
Q4 GGUF baseline.
