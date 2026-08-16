# OpenCode plus Qwen3-Coder 30B: restricted qualification

**Date:** 2026-08-16  
**Scope:** one disposable coding canary; not a broader model ranking.

## Result

OpenCode `1.18.18` completed the `normalize_tag` correction through the same
loopback-only llama-server and Qwen3-Coder 30B GGUF used in the local-harness
qualification. It ran as the restricted `llm-runner` Unix user with `--pure`
and an isolated XDG profile.

- The fixture started failing and the final standard-library test passed.
- The OpenCode CLI wall time was **17.782 seconds**.
- It first attempted a relative read that its local adapter rendered as
  `/module.py`; the external-directory rule correctly rejected that path.
- It then used the permitted workspace shell to overwrite `module.py`, ran the
  test successfully, and made one extra direct Python verification.
- The profile denied external directories, web fetch/search, subagents, skills,
  LSP, questions, and loop recovery. No canonical repository or credential was
  available to `llm-runner`.

This is useful as a practical local coding harness. It is not an application-
level replacement for the Unix boundary: normal workspace shell access is
needed with this adapter because the exact-path edit profile did not match the
adapter's absolute-path representation.

## Timing comparison: same small correction

| Harness | Result | Measured execution wall time | Important context |
|---|---|---:|---|
| Minimal local harness | passed | 2.727 s tool loop | One generic tool, four prescribed actions, 64K llama-server. |
| OpenCode practical profile | passed | 17.782 s | Normal workspace shell/edit/read; external, web, subagent, and skill paths denied. |
| Qwen Code 0.21.12 | passed | 46.268 s | Earlier restricted canary; broad platform tool registration and one rejected post-success goal call. |

These are directional measurements, not a fair performance ranking: the
harnesses inject different prompts, tool inventories, and turn structures.
They do show that OpenCode completed this task materially faster than the prior
Qwen Code run and with a much smaller observed tool surface, while the minimal
direct harness remains the lowest-overhead controlled path.

## Decision

Keep both paths:

1. Use the minimal local harness for controlled model qualification and
   reproducible tool-contract tests.
2. Use OpenCode's practical profile for the next realistic local-agent canary,
   still only under `llm-runner` and in a dedicated worktree.
3. Do not use Qwen Code as the default local harness until its built-in tool
   registration can be constrained more effectively.

## Cleanup

The temporary llama-server process was stopped and `ollama ps` was empty at
completion. OpenCode was installed only in `/srv/llm-runner/.opencode`; no
system package, Ollama setting, Open WebUI setting, listener, or canonical
repository changed.
