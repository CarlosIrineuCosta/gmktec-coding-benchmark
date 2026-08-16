# Qwen Code plus Qwen3-Coder 30B: restricted canary result

**Date:** 2026-08-16

## Result

The Qwen Code `0.21.12` harness completed the disposable Python correction as
the non-privileged `llm-runner` user.

- Model: Qwen3-Coder 30B, same existing GGUF used by the llama-server A/B.
- Serving: loopback-only llama-server at 64K; stopped immediately afterward.
- Workspace: `/srv/llm-runner/workspaces/qwen-code-canary`.
- Boundary proof: `llm-runner` could not read `cdc`'s SSH key or AI secret file.
- Preflight: plan mode returned exactly `READY`; no file write.
- Execution: one read, one exact edit of `module.py`, one allowed
  `python3 test_canary.py` invocation; test exited zero.
- Final verification: the corrected function is `value.strip().lower()`.

No canonical repository, Open WebUI connection, public/Tailscale listener, or
Ollama configuration changed. `ollama ps` was empty after stopping the server.

## Harness observations

The Qwen Code framework remains much heavier than the minimal Floor loop:

| Phase | Model turns | Total input tokens | Duration |
|---|---:|---:|---:|
| Plan-mode preflight | 1 | 67,183 | 60.611 s |
| Edit/test turn | 6 | 119,617 | 46.268 s |

The large token totals are primarily repeated framework/tool context and cache
accounting, not task content. Even after the documented `tools.core` allowlist,
Qwen Code 0.21.12 still registered platform-level computer, goal, task, and
agent tools. The model did not call any of those before completing the useful
work, but it made one unnecessary `update_goal` call after reporting success;
the harness rejected it because no active goal existed.

Therefore this result proves a narrow point: Qwen Code plus llama-server can
make and validate a small code correction under the restricted Unix account.
It does **not** yet qualify Qwen Code as the clean controlled harness for the
larger benchmark. A next comparison should either remove the residual
platform-level tools at registration time or use the minimal Floor tool loop as
the controlled baseline.
