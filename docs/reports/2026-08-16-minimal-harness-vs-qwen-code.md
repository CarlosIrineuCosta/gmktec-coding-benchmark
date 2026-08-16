# Qwen3-Coder 30B: minimal local harness versus Qwen Code

**Date:** 2026-08-16  
**Scope:** small fully specified coding canaries only; this is not a ranking of
Qwen3-Coder nor a larger Floor benchmark result.

## Controlled conditions

- Inference: Qwen3-Coder 30B, the existing SHA-256
  `1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a`
  GGUF (`Q4_K - Medium`).
- Server: loopback-only llama-server build `b10454-4df29be4f4c3673f428170fda944a5b19f743bb8`, Jinja template, 64K context, one model process.
- Execution identity: the restricted Unix user `llm-runner`; its only writable
  surfaces were its private workspace, profile, runtime, and logs.
- Tasks: three disposable, standard-library two-file Python corrections. Each
  fixture began with a failing test and stated the required outcome and exact
  test command. There were no hidden tests, packages, network access,
  credentials, or canonical repository files.

## Minimal local harness result

The minimal harness requires an exact preflight `READY`, then exposes only one
function with three bounded actions: read either supplied file, overwrite only
`module.py`, or run only `python3 test_canary.py`. It rejects path escapes,
unknown actions, malformed JSON, and more than one tool call in a turn.

| Canary | Result | Model calls | Preflight | Execution tool-loop |
|---|---:|---:|---:|---:|
| `normalize_tag` | passed | 5 | 240 ms | 2.727 s |
| `parse_priority` | passed | 5 | 217 ms | 2.574 s |
| `render_label` | passed | 5 | 225 ms | 2.619 s |

All three runs were then repeated solely after correcting Prometheus metrics
capture; the table reports that repeat. Each preflight returned exactly
`READY`. Each execution made exactly four permitted calls in the expected
shape: read `module.py`, read `test_canary.py`, write `module.py`, run the
test. Every final test passed. The saved private results include `/props` and
the Prometheus `/metrics` snapshots; `/props` confirmed effective `n_ctx=65536`.

This establishes a usable controlled baseline: the model can follow this small
single-tool contract and make a correct bounded repair when the task is fully
specified.

## Qwen Code matched preflight result

The matched Qwen Code attempt used version `0.21.12`, the same local server,
the same restricted user, the same `normalize_tag` fixture, and plan mode. It
did not satisfy the preflight contract, so the other two Qwen Code tasks were
intentionally not run.

- It registered a broad tool surface despite the configured core-tool list:
  computer-control, goal/task, agent, skill, filesystem, and shell tools.
- It emitted `READY` but continued with `read_file` twice and an attempted
  `run_shell_command`, instead of stopping after the exact preflight response.
- Plan mode denied the shell invocation. It did not write the fixture.
- The run ended after four model turns in 50.488 seconds. Qwen Code reported
  81,749 input tokens, 587 output tokens, and 61,346 cached input tokens.

This is a Qwen Code interface-contract block, not a model coding failure. It
also demonstrates why the minimal harness and Qwen Code cannot presently be
treated as equivalent benchmark environments: the latter injects much more
tool and platform context and does not currently honour the exact no-tool
preflight gate.

## Decision for the next pass

Use the minimal local harness as the controlled Qwen3-Coder qualification
path. Keep Qwen Code as a separate full-agent experiment until its tool
registration can be narrowed at the runtime level, not merely requested in a
profile. Do not score the unmatched Qwen Code preflight against the model or
use it for the wider task comparison.

## Cleanup

The temporary llama-server process was verified stopped at completion; no model
was resident in Ollama. No system package, driver, Ollama configuration, Open
WebUI setting, listener, credential, or canonical repository changed.
