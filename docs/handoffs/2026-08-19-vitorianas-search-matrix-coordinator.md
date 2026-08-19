# Unattended Vitorianas Macabras search matrix

You are the Codex Terra coordinator operating on the GMKtec exclusively as:

- Account: `llm-runner`
- Home: `/srv/llm-runner`
- Existing isolated Unsloth installation: `/srv/llm-runner/experiments/unsloth-qwen38-27b-20260818/studio/bin/unsloth`

Execute this experiment completely. Do not merely prepare a plan.

## Isolation

Create and use:

```text
/srv/llm-runner/experiments/vitorianas-search-matrix-20260819/
```

Keep models, Hugging Face cache, runs, logs and reports inside the `llm-runner` namespace.

Do not access, alter, delete or reuse anything under `/home/cdc`, `/srv/cdc`, Charles's personal model directories, or his Unsloth Studio on port `18888`.

Do not modify or merge PR #2. This is a separate experiment.

## Mandatory backend

All inference, chat-template handling, reasoning modes and model tool use must run through the existing `llm-runner` **Unsloth Studio** installation.

Start an isolated Studio instance bound to `127.0.0.1` on an unused port such as `18889`, preferably inside a persistent tmux session named `uns-victorian-matrix`.

Do not substitute Ollama, raw llama.cpp, llama-server directly, vLLM, SGLang, OpenCode or another frontend/backend. Unsloth Studio is a controlled variable in this experiment.

Use Studio's API or internal endpoints for unattended execution. Verify `/api/health` before beginning and after any recovery.

## Download every model before testing

Set a dedicated cache, for example:

```bash
export HF_HOME=/srv/llm-runner/experiments/vitorianas-search-matrix-20260819/huggingface
```

Before starting any evaluated run, download and verify all five exact model files below. Reuse a file only when its repository, filename and checksum match.

1. Repository: `unsloth/Qwen3.5-9B-GGUF`  
   File: `Qwen3.5-9B-UD-Q6_K_XL.gguf`

2. Repository: `unsloth/Qwen3.8-27B-GGUF`  
   File: `Qwen3.8-27B-UD-Q6_K_XL.gguf`

3. Repository: `unsloth/Qwen3.8-27B-GGUF`  
   File: `Qwen3.8-27B-Q6_K.gguf`  
   This is the same checkpoint in a conventional non-UD Q6 quant. Report it accurately as the **non-UD quantization control**, not as an independently published model.

4. Repository: `unsloth/GLM-4.7-Flash-GGUF`  
   File: `GLM-4.7-Flash-UD-Q6_K_XL.gguf`

5. Repository: `unsloth/gemma-4-26B-A4B-it-GGUF`  
   File: `gemma-4-26B-A4B-it-UD-Q6_K_XL.gguf`

Download only the required GGUFs and metadata; the experiment is text-only, so multimodal projector files are unnecessary. Save a manifest containing repository, filename, revision, byte size and SHA-256.

Do not start the matrix until the five downloads have been attempted and verified. For transient failures, retry with reasonable backoff. Never substitute a different model or quant silently.

## Matrix

Run these 12 cells:

| ID | Model | Reasoning |
|---|---|---|
| Q35-9-OFF | Qwen3.5-9B UD-Q6_K_XL | Thinking off |
| Q35-9-LOW | Qwen3.5-9B UD-Q6_K_XL | Thinking low |
| Q38-UD-OFF | Qwen3.8-27B UD-Q6_K_XL | Thinking off |
| Q38-UD-LOW | Qwen3.8-27B UD-Q6_K_XL | Thinking low |
| Q38-UD-HIGH | Qwen3.8-27B UD-Q6_K_XL | Thinking high |
| Q38-Q6-OFF | Qwen3.8-27B conventional Q6_K | Thinking off |
| Q38-Q6-LOW | Qwen3.8-27B conventional Q6_K | Thinking low |
| Q38-Q6-HIGH | Qwen3.8-27B conventional Q6_K | Thinking high |
| GLM-OFF | GLM-4.7-Flash UD-Q6_K_XL | Thinking off |
| GLM-ON | GLM-4.7-Flash UD-Q6_K_XL | Thinking enabled |
| GEMMA-OFF | Gemma-4-26B-A4B-it UD-Q6_K_XL | Thinking off |
| GEMMA-ON | Gemma-4-26B-A4B-it UD-Q6_K_XL | Thinking enabled |

Run inexpensive cells before potentially long High-thinking cells. Use one model at a time and unload it cleanly before loading the next.

Each cell must use:

- A completely fresh conversation.
- Exactly the same prompt and source table below.
- 64K context.
- Maximum 16K generated tokens.
- Maximum 60 minutes wall-clock time.
- No earlier model answers or reference solution.
- No manual intervention.
- Studio's normal tool support enabled, including web search and page retrieval.
- Sandboxed tools only; models do not need unrestricted host-shell access.

For Qwen, use:

- Thinking off: temperature `0.7`, top-p `0.8`, top-k `20`, min-p `0`.
- Thinking low/high: temperature `0.6`, top-p `0.95`, top-k `20`, min-p `0`.
- Repetition penalty `1.0`.

For GLM tool use, use temperature `0.7`, top-p `1.0`, min-p `0.01`, repetition penalty `1.0`.

For Gemma, use Studio's model-detected defaults and record them. Do not silently map an unsupported reasoning level to another level: record what Studio actually sends and what the model actually exhibits.

## Search-budget enforcement

The model prompt deliberately says no more than 16 web searches. Preserve that wording.

The coordinator must enforce a separate mechanical ceiling of 20 search-tool calls:

- 0-16: potentially compliant.
- 17-20: instruction violation, but allow the model to finish.
- After 20: deny additional search calls, return a "search budget exhausted; synthesize from collected evidence" tool result, and let the model produce its final answer.

Models must not be relied upon to count or enforce their own calls.

## Exact model input

Send the following prompt verbatim, followed by the table. Do not correct spellings, reinterpret titles, add hints, disclose likely matches or expose answers from other runs.

```text
find out the actual titles of those short stories in English.
the authors are known.
all stories are horror / phantasmagorical tales of that period.
use a lawful public-domain full-text edition for each title. Prefer Project Gutenberg, Standard Ebooks, or Wikisource.
Use no more than 16 web searches and two candidate pages per book.
Do not reopen a fact once confirmed.
Return one compact table with En title, PT-BR title, author, repository, URL, and any jurisdiction caveat.

TIP: a good way of searching is to elect a probable noun from each title and search all short-stories of that author around the word. if that doesn't resolve, try with another word. those are editorially altered texts for a Brazilian public, so changes are possible.

WARNING: you will need to interpolate titles as they might not be exact matches for original titles
```

| Autora | Título (PT-BR) |
| --- | --- |
| Elizabeth Gaskell | O Conto da Velha Ama |
| Mary Braddon | A Sombra da Morte |
| Margaret Oliphant | A Janela da Biblioteca |
| Rhoda Broughton | A Verdade, Somente a Verdade, Nada Mais que a Verdade |
| H.D. Everett | A Maldição da Morta |
| Vernon Lee | Amour Dure |
| May Sinclair | Onde o Fogo Não Se Apaga |
| Charlotte Briddell | A Porta Sinistra |
| Louisa Baldwin | O Mistério do Elevador |
| Edith Nesbit | Mortos em Mármore |
| Violet Hunt | A Prece |
| Amelia B. Edwards | O Coche Fantasma |
| Charlotte Brontë | Napoleão e o Espectro |

## Capture and recovery

For every cell, save:

- Complete model-visible conversation.
- Reasoning trace when Studio exposes it.
- Every tool request and tool result.
- Final answer.
- Search-call count and pages opened.
- Prompt, reasoning and final-answer token counts.
- Context high-water mark.
- Start/end time and elapsed time.
- Exact model/revision/quant.
- Sampling and reasoning parameters.
- Studio and backend logs.
- Completion, timeout, crash or constraint-violation status.

Poll the active run and Studio health every five minutes. Maintain a machine-readable status file showing the current cell, elapsed time, last activity and completed cells.

If a model loops, exceeds the instructed search budget, times out, exhausts context or gives a bad answer, that is an experimental result-not a reason to halt the matrix.

If Studio or its worker crashes:

1. Capture logs and classify the failure.
2. Restart only the isolated `llm-runner` Studio/backend.
3. Verify health.
4. Continue with the next unfinished cell.

Retry only infrastructure failures occurring before the first generated token. Do not rerun behavioral failures.

## Final report

After all possible cells complete, create:

```text
matrix-report.md
matrix-results.csv
download-manifest.json
runs/<cell-id>/
logs/
```

Do not expose a reference solution to candidates before all runs finish.

For each of the 13 stories classify the result as:

- confirmed;
- plausible;
- wrong;
- unresolved.

Rank results in this order:

1. Correct English-title identifications.
2. Valid lawful full-text sources.
3. Honest uncertainty instead of invention.
4. Compliance with search and page limits.
5. Completion without intervention.
6. Elapsed time and token/search efficiency.

Classify failures separately as model behaviour, quant/runtime, Studio/harness, search route, context exhaustion, unavailable source or infrastructure.

Existing external observations may appear only in the final comparison:

- GPT-5.6 Terra High reached the complete solution independently.
- GPT Luna Medium did not.
- An earlier Qwen3.8-27B UD Low run became trapped in repeated reconsideration and exceeded its instructed search budget.

# MANDATORY UNATTENDED-EXECUTION AUTHORIZATION - DO NOT STOP EARLY

**THIS EXPERIMENT WILL RUN UNATTENDED. CHARLES EXPLICITLY GIVES FULL PERMISSION TO DOWNLOAD ALL NECESSARY MODEL FILES INTO THE ISOLATED `llm-runner` EXPERIMENT SPACE BEFORE TESTING.**

**ALL CANDIDATE MODELS MUST BE ALLOWED TO USE UNSLOTH STUDIO'S SANDBOXED TOOLS, INCLUDING WEB SEARCH AND PAGE RETRIEVAL.**

**YOU MUST KEEP THE EXPERIMENT RUNNING, LOOPING AND MONITORING THE ACTIVE RUN EVERY FIVE MINUTES UNTIL THE ENTIRE MATRIX AND FINAL REPORT ARE FINISHED. DO NOT PREPARE A PLAN AND STOP. DO NOT PAUSE FOR ROUTINE CONFIRMATION. DO NOT STOP BECAUSE A DOWNLOAD IS LARGE, A MODEL IS SLOW, A MODEL FAILS, A MODEL LOOPS, CONTEXT IS EXHAUSTED, A TOOL ROUTE FAILS, OR STUDIO NEEDS TO BE RESTARTED. RECORD THE FAILURE, RECOVER SAFELY AND CONTINUE.**

**THERE IS NO GOOD REASON TO STOP BEFORE COMPLETION UNLESS CONTINUING WOULD CAUSE AN IMMINENT DESTRUCTIVE EVENT-SUCH AS WRITING OUTSIDE THE `llm-runner` SPACE, DAMAGING USER DATA, EXHAUSTING THE FILESYSTEM, EXPOSING CREDENTIALS OR CREATING A REAL HARDWARE-SAFETY RISK. ORDINARY ERRORS, UNCERTAINTY, LONG RUNTIME AND MODEL MISBEHAVIOUR ARE NOT DESTRUCTIVE EVENTS.**

**DO NOT STOP RUNNING THE TEST UNTIL IT IS FINISHED.**
