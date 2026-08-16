# Qwen Code plus Qwen3-Coder 30B qualification: blocked before model execution

**Date:** 2026-08-16
**Classification:** first pass stopped before the edit/test phase. It produced
two separate findings: runner isolation was initially unavailable, then Qwen
Code's default tool contract failed the read-only preflight gate. Neither is a
Qwen3-Coder coding-quality result.

## Intended qualification

- Harness: Qwen Code `0.21.12`.
- Inference: Qwen3-Coder 30B through the existing loopback-only llama-server
  launcher, using the same GGUF already recorded for the local backend A/B.
- Context: 64K; temperature zero; no fallback model; no automatic retry.
- Profile: isolated through `QWEN_HOME=/home/cdc/llm/qwen-code/profile` and
  `QWEN_RUNTIME_DIR=/home/cdc/llm/qwen-code/runtime`.
- Task: a disposable standard-library Python canary. It began in a known
  failing state and was intentionally designed to require no package install.

The profile template is tracked at
`deploy/gmktec/qwen-code-qwen3-coder-30b-settings.json`. It targets only
`http://127.0.0.1:8081/v1`.

## Initial isolation blocker

Qwen Code can execute shell commands and inspect files. It must therefore run
inside a filesystem-confined worktree. The required isolation mechanism is not
available on GMKtec:

| Probe | Result |
|---|---|
| `bwrap` | not installed |
| transient user-systemd mount sandbox | failed with `status=226/NAMESPACE`: mount namespacing unsupported |
| `unshare --user --map-root-user --mount /bin/true` | failed: `/proc/self/uid_map: Operation not permitted` |

Running Qwen Code as `cdc` without that boundary would permit host inspection
outside the disposable worktree. A non-privileged fallback account was therefore
created before any model turn.

## Restricted-account proof

The `llm-runner` account has only its primary group, a locked password, and a
private `/srv/llm-runner` home. Its SSH session could write the disposable
workspace/profile but could not read either `cdc`'s SSH key or its AI secret
file. This is a Unix-user boundary, not a container: network egress and
world-readable system files are still in scope.

## Qwen Code preflight finding

The first preflight was run as `llm-runner` using Qwen Code `0.21.12`, Qwen3-
Coder 30B through loopback llama-server at 64K, and a known-failing,
standard-library-only canary. It was instructed to inspect, then answer only
`READY` or `MISSING`, with no edits.

Instead, its initialization exposed a broad default tool surface including
filesystem tools, `web_fetch`, computer-control tools, goal/task controls, and
sub-session controls. No MCP server was configured. The model read the two
task files but did not return `READY` or `MISSING`; it entered a loop using
`todo_write` and invalid `update_goal` calls. It made no file write. The run
was stopped manually and the fixture remained unchanged.

This is a harness-contract result: Qwen Code's default prompt/tool environment
is too large for the controlled sequential-tool comparison. The recorded first
model turn also carried approximately 15.8K input tokens on this tiny canary,
mostly the harness/tool context. Do not score this as a Qwen model failure.

Before a second Qwen Code attempt, identify and disable the unneeded built-in
tool groups, or run it only in a deliberately separate full-agent comparison.
The controlled baseline remains the minimal Floor tool loop with an explicit
allowlist.

## Cleanup and next condition

The temporary llama-server process was stopped cleanly; `ollama ps` was empty
afterward. No Open WebUI connection, public/Tailscale listener, model file, or
Ollama configuration was changed.

Before resuming, provide one approved runner mechanism that can mount a
read-only runtime and a writable worktree/profile while hiding the rest of the
host filesystem. The validation proof is: the harness can read/write its
worktree and profile, but cannot stat `/home/cdc/.ssh`. After that proof, run
the Qwen Code preflight first, then its edit/test turn. Do not classify this
block as a Qwen Code or Qwen3-Coder failure.
