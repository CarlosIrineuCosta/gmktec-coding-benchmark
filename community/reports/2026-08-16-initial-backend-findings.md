# Initial Ollama tool-loop findings on a Strix Halo mini PC

**Date:** 2026-08-16

**Status:** preliminary diagnostic evidence; not a model ranking

## Question

Can two locally served models complete a fully specified, minimal Python edit
through a native tool loop, and does their behavior justify a controlled
Ollama-versus-`llama-server` comparison?

## Canary contract

Each model received an isolated two-file Python task. It was told which three
tools existed (`read_file`, `write_file`, and `run_test`), asked whether any
information was missing, then asked to make one minimal normalization fix and
run the supplied test.

Settings:

- context requested: 8,192 tokens;
- generation cap: 1,024 tokens per response;
- temperature: 0;
- reasoning display disabled by the serving request;
- no packages or network access;
- prompt requested at most one tool call per turn.

## GPT-OSS 120B observation

The model first requested the two files, then used the available tools after
their availability was made explicit. It read each file once, wrote once, ran
the test once, and stopped.

| Metric | Observation |
|---|---:|
| Wall time | 38.30 seconds |
| Tool calls | 4 |
| Reads | 2 |
| Writes | 1 |
| Test calls | 1 |
| Final test | 1 passed |

In an earlier 65,536-context coding pass, the same Ollama model route returned
HTTP 500 before producing tool-loop work. The successful 8K canary shows that
basic tool use works; it does not identify whether the earlier failure came
from context allocation, memory pressure, model configuration, or another
server condition.

## GLM-4.6V Flash 9B observation

The model said it was ready, read both files, and wrote the correct minimal
fix. The final test passed. However, it emitted 167 parsed tool calls, including
164 requests to run the same test.

| Metric | Observation |
|---|---:|
| Wall time | 146.89 seconds |
| Tool calls | 167 |
| Reads | 2 |
| Writes | 1 |
| Test calls | 164 |
| Final test | 1 passed |

This is not a safe agent loop. The observation does not yet distinguish model
generation from chat-template, tool-parser, backend, or client-loop behavior.

## Backend relevance

The community Strix Halo guide recommends Ollama as the easiest private-chat
path and recommends `llama-server` for local APIs, several tools, long-context
tests, and server experiments. The latter description more closely matches a
coding-agent benchmark.

Sources:

- <https://github.com/hogeheer499-commits/strix-halo-guide/blob/main/STRIX_HALO_LOCAL_LLM_SETUP.md>
- <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- <https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md>

This warrants a controlled backend comparison. It does not establish that
Ollama caused the repeated calls or cannot support coding agents.

## Minimal next experiment

Use the same underlying weights, quantization, chat template, prompt, tools,
context, generation cap, and hardware state through both backends. Run the
canary three times at 8K, then increase to 16K, 32K, and 64K only while serving
remains stable. Record raw assistant output before parsing, total and unique
tool calls, effective context/KV allocation, memory, timings, and stop reason.

Parallel tool calls should be disabled or rejected unless explicitly part of
the experiment. No conclusion about model quality should be drawn from this
canary alone.
