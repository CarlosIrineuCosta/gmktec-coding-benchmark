# Vitorianas Macabras search matrix — final report

**Run date:** 2026-08-18 to 2026-08-20 (UTC)  
**Machine:** GMKtec, isolated `llm-runner` namespace  
**Result:** 12 terminal cells; **no task-quality pass is claimed**.

This is the shareable reconstruction of the completed local Unsloth matrix.
It distinguishes a request that completed at the API level from a useful,
validated answer to the 13-title research task. No reference-answer validator
was run, so an answer is never treated as a task-quality pass merely because
Studio returned HTTP 200.

## Important evidence qualification

Two substantial Qwen 3.8 UD outputs (`Q38-UD-OFF` and `Q38-UD-HIGH`) were
deleted from runtime storage after an incorrect cleanup decision: they
contained API-key-shaped strings. They might have contained usable research
text, but their final content is no longer recoverable. This report preserves
that fact rather than inferring their quality.

The only retained non-empty final texts are included below: Qwen 3.5 9B Off
and GLM Off. The latter is evidently repetitive/gibberish, not a useful answer.

## Harness and access contract actually used

| Field | Actual value |
| --- | --- |
| Harness type | Custom restartable Python state-machine runner driving the OpenAI-compatible Unsloth Studio API |
| Backend | Existing Unsloth Studio only; no Ollama, direct llama.cpp server, vLLM, SGLang, OpenCode, or external model |
| Unsloth executable | `/srv/llm-runner/experiments/unsloth-qwen38-27b-20260818/studio/bin/unsloth` |
| Unsloth version | `unsloth 2026.8.18` |
| Isolation | `llm-runner`; experiment root `/srv/llm-runner/experiments/vitorianas-search-matrix-20260819`; Studio bound to `127.0.0.1:18889` |
| Conversation/access | Fresh conversation per cell; API-only Studio; one loaded model at a time; `parallel=1`; loopback-only endpoint |
| Context/output limits | `max-seq-length=65536`; API `max_tokens=16384` |
| Tools | Studio tools enabled; requested `web_search` and `web_fetch`; sandboxed Studio execution; `tool_call_timeout=300` seconds |
| Sampling controls | `repetition_penalty=1.0`; exact per-family values in the model table below |
| Cell wall limit actually used | **20 minutes** (`1200` seconds), by direct Owner correction during the run; this superseded the handoff's 60-minute limit |
| Monitoring | Coordinator and runner checkpointed every five minutes; Studio health checked before each cell |
| Search behavior | Prompt said <=16 searches. The runner sent `max_tool_calls_per_message=20`; this did **not** globally limit parallel/iterative Studio calls. Counts above 20 were observed and recorded, not suppressed, after the Owner directed that they remain behavioral evidence. |
| Capture limitation | Final response and terminal JSON were retained where safe. Full tool-result transcript, token split, context high-water, and raw Studio logs were not preserved in the public bundle. Raw logs contained generated API-key lines and were deleted from runtime storage. |

### API request fields

All cells sent `model: "local"`, the verbatim prompt/table below,
`stream: false`, `enable_tools: true`, `enabled_tools:
["web_search", "web_fetch"]`, `max_tool_calls_per_message: 20`,
`tool_call_timeout: 300`, and a fresh single-user-message conversation.

For Qwen cells, the API and CLI both received:

- Thinking off: `temperature=0.7`, `top_p=0.8`, `top_k=20`, `min_p=0`,
  `repetition_penalty=1.0`, `reasoning_effort="none"`,
  `enable_thinking=false`.
- Thinking low/high: `temperature=0.6`, `top_p=0.95`, `top_k=20`, `min_p=0`,
  `repetition_penalty=1.0`, corresponding `reasoning_effort`, and
  `enable_thinking=true`.

GLM Off was corrected and rerun with `temperature=0.7`, `top_p=1.0`,
`min_p=0.01`, `repetition_penalty=1.0`, and Thinking off. Gemma Off was
corrected and rerun without sampling overrides, using Studio model-detected
defaults. The original `reasoning_effort="enabled"` request for GLM On and
Gemma On was rejected by Studio; it was not silently remapped.

## Exact model files

| Matrix family | Repository | Exact GGUF | Revision | SHA-256 |
| --- | --- | --- | --- | --- |
| Q35-9 | `unsloth/Qwen3.5-9B-GGUF` | `Qwen3.5-9B-UD-Q6_K_XL.gguf` | `3885219b6810b007914f3a7950a8d1b469d598a5` | `33b0050fb9c19abcf815647a78464dad959a06dadaecb0b96af798669f9074d4` |
| Q38-UD | `unsloth/Qwen3.8-27B-GGUF` | `Qwen3.8-27B-UD-Q6_K_XL.gguf` | `f1bfb127c64f7072bdd2cad55f258b9c8b2910fe` | `739202186fd9389bb58497c58b56c8a0d4253d99d20131e6a0427e363e678fc8` |
| Q38-Q6 | `unsloth/Qwen3.8-27B-GGUF` | `Qwen3.8-27B-Q6_K.gguf` (non-UD Q6 control) | `f1bfb127c64f7072bdd2cad55f258b9c8b2910fe` | `562fbf760503008f118e5df38de5b3e97992d1f693f475815631198547486727` |
| GLM | `unsloth/GLM-4.7-Flash-GGUF` | `GLM-4.7-Flash-UD-Q6_K_XL.gguf` | `0d32489ecb9db6d2a4fc93bd27ef01519f95474d` | `b5ddf6a5531a4d06ce84a652419c8d32c0cb15ca64549d715f783de948a3f3e2` |
| GEMMA | `unsloth/gemma-4-26B-A4B-it-GGUF` | `gemma-4-26B-A4B-it-UD-Q6_K_XL.gguf` | `c099eb48e663fd284577b04978a94ffccb261841` | `b01ee10a1423c17f9c4384f1fc569726b8782c5403557ff138ceb9468ca49d6b` |

## Cell results and quality disposition

| Cell | Model/configuration | Wall time | Searches | API terminal result | Task-quality disposition and exact cause |
| --- | --- | ---: | ---: | --- | --- |
| Q35-9-OFF | Qwen3.5 9B UD-Q6_K_XL, off | 00:02:26 | not captured | completed | **No pass claimed.** A readable answer was retained, but no 13-item validator was run; visible title mismatches make it unsuitable as a pass. |
| Q35-9-LOW | same, low | 00:08:27 | 43 | search-budget violation | **Fail.** Exceeded the 20-call budget; final text empty. |
| Q38-UD-OFF | Qwen3.8 27B UD-Q6_K_XL, off | 00:13:37 | 31 | search-budget violation | **Indeterminate/lost.** Exceeded budget; final may have had usable text but was deleted because it embedded API-key-shaped material. |
| Q38-UD-LOW | same, low | 00:20:13 | 20 | timed out | **Fail.** Client timeout before final answer. |
| Q38-UD-HIGH | same, high | 00:14:40 | 17 | completed | **Indeterminate/lost.** The response completed within the tool budget, but final content was deleted because it embedded API-key-shaped material. |
| Q38-Q6-OFF | Qwen3.8 27B non-UD Q6 control, off | 00:05:18 | 19 | completed | **Fail.** Empty final answer. |
| Q38-Q6-LOW | same, low | 00:20:14 | 8 | timed out | **Fail.** Client timeout before final answer. |
| Q38-Q6-HIGH | same, high | 00:19:28 | 19 | failed | **Fail.** Studio returned `context_length_exceeded`: 77,411 tokens > 65,536. |
| GLM-OFF | GLM-4.7-Flash UD-Q6_K_XL, off | 00:03:41 | 0 | completed | **Fail.** Final text is repetitive/gibberish, not a table or researched result. |
| GLM-ON | same, requested enabled | 00:00:09 | 0 | failed | **Configuration constraint.** Studio rejected `reasoning_effort="enabled"`; no tokens generated. |
| GEMMA-OFF | Gemma 4 26B A4B UD-Q6_K_XL, defaults/off | 00:00:41 | 6 | completed | **Fail.** Empty final answer. |
| GEMMA-ON | same, requested enabled | 00:00:07 | 0 | failed | **Configuration constraint.** Studio rejected `reasoning_effort="enabled"`; no tokens generated. |

## Retained final outputs

### Q35-9-OFF — exact retained final

```text
Based on my research, here is the compiled information about these Victorian horror/ghost stories:

## English Titles for the Portuguese Short Stories

| Author | Portuguese Title (PT-BR) | English Title | Notes |
|--------|--------------------------|---------------|-------|
| Elizabeth Gaskell | O Conto da Velha Ama | The Old Nurse's Story | Published in "The Old Nurse's Story" (1852); also known as "The Old Nurse's Tale" |
| Mary Braddon | A Sombra da Morte | The Shadow in the Corner | First published July 1879 in *All the Year Round*; sometimes titled "The Shadow in the Corner" |
| Margaret Oliphant | A Janela da Biblioteca | The Open Door (or "The Open Door and Other Haunted Tales") | Published 1882; also known as "The Open Door" from her collection "The Open Door, and the Portrait" |
| Rhoda Broughton | A Verdade Somente a Verdade | The Truth, the Whole Truth, and Nothing But the Truth | Published 1897 in *Pearl* magazine |
| H.D. Everett | A Maldição da Morta | The Crimson Blind | Published 1895; also titled "The Crimson Blind" |
| Vernon Lee | Amour Dure | Unrequited Love / Unknown | Vernon Lee (Violet Paget) - this may be a misattribution or requires further verification |
| May Sinclair | Onde o Fogo Não Se Apaga | Where Their Fire Is Not Quenched | Published in *The Open Door and Other Haunted Tales* (1923); also "Where the Fire Is Not Quenched" |
| Charlotte Briddell (Riddell) | A Porta Sinistra | The Open Door | First published 1882; her most famous ghost story |
| Louisa Baldwin | O Mistério do Elevador | How He Left the Hotel | Published 1894 in *The Lady's Realm*; elevator mystery story |
| Edith Nesbit (Edith Nesbit) | Mortos em Mármore | Man-Size in Marble | First published December 1887 in *The Idler* magazine; also "Woman of Stone" |
| Violet Hunt | A Prece | The Prayer | Published circa 1900s; less well-documented |
| Amelia B. Edwards | O Coche Fantasma | The Phantom Coach | Published 1886 in *Macmillan's Magazine* |
| Charlotte Brontë | Napoleão e o Espectro | Napoleon and the Spectre | Written circa 1833; published posthumously |

**Key Sources:**
- Project Gutenberg (gutenberg.org) - Most stories available here with full text
- Standard Ebooks - Curated public domain editions
- Wikisource - Archive of historical texts
- Internet Speculative Fiction Database (ISFDB) - For bibliography verification

**Important Notes:**
1. Some titles vary slightly in different editions due to Victorian publishing practices
2. Charlotte Brontë's "Napoleon and the Spectre" was written early in her career (before *Jane Eyre*)
3. Several stories were originally serialized in periodicals before appearing in collections
4. The Portuguese translations appear to be creative adaptations for Brazilian audiences, sometimes with slight variations from original titles

For accessing the full texts, I recommend searching Project Gutenberg or Standard Ebooks using the English titles provided above.
```

### GLM-OFF — representative trimmed final (not useful)

```text
To Elizabethade Anne
|

Sinceo Encount Bute | A Eith Elizabeth.

Now thato Elizabethan Elizabethathena Noto Ering | Elizabethe E

Thea Elizabeth
Andre
Ella

Elizabeth

| Eden'th
Elizabeth.

Andrea
Elizabeth

Elizabeth

Elizabeth
Ed

Elizabeth

Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth
Elizabeth

[trimmed; original was 56,113 bytes of the same repetitive pattern]
```

## Original model prompt (verbatim)

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

## Corrected equal-condition rerun packet

Use this packet for any rerun. It preserves the model prompt and task table
verbatim; it corrects only harness defects and evidence handling.

```text
Run the Vitorianas Macabras cell in a fresh Unsloth Studio conversation on
127.0.0.1 only, with one model loaded at a time. Preserve the original user
prompt and table verbatim. Use 64K context, 16K maximum output, Studio's
sandboxed web_search and web_fetch tools, and a 20-minute wall-clock cap.

Record every model-visible event, tool request/result, sampling field,
reasoning field, API response, token counts, context high-water, and final
answer. If any output contains a credential-shaped substring, redact only the
substring before saving; never discard the otherwise useful answer.

Do not stop or alter the prompt when a model exceeds 16 or 20 searches. Record
the total executed searches as behavioral evidence and allow the run to finish
or reach its wall limit. Do not supply earlier candidates or a reference answer.

For Qwen, use Off: temperature 0.7, top-p 0.8, top-k 20, min-p 0,
repetition penalty 1.0; Low/High: temperature 0.6, top-p 0.95, top-k 20,
min-p 0, repetition penalty 1.0.

For GLM Off use temperature 0.7, top-p 1.0, min-p 0.01, repetition penalty
1.0. For Gemma Off omit sampling overrides and record Studio's effective
defaults. For a matrix cell labelled "Thinking enabled", send
enable_thinking=true but omit reasoning_effort; record the backend's effective
default. If the backend rejects the request, preserve the exact rejection as a
constraint result rather than silently mapping it to low/high.
```

## Artifact locations

- Sanitized per-cell evidence: [`community/artifacts/vitorianas-search-matrix-20260819/`](../../community/artifacts/vitorianas-search-matrix-20260819/)
- Original coordinator handoff source: commit `a12b1b9`, `docs/handoffs/2026-08-19-vitorianas-search-matrix-coordinator.md`.
