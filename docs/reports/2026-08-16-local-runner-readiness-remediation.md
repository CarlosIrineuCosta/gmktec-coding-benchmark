# Local-runner readiness remediation

Status: Qwen/OpenCode is now qualified for a new local task.  No other local
model is implicitly qualified by this result.

## Failure corrected

The first OpenCode Historical run executed as `llm-runner`, but pytest had only
been checked in a `cdc`-owned environment.  The actual runner therefore had no
`pytest` module.  This was a controller-provisioning failure.

## Correction and evidence

- Created runner-owned `/srv/llm-runner/venv` on GMKtec.
- Installed pinned `pytest==9.1.1` there.
- Added a tracked bootstrap script and fail-closed readiness script.
- Ran the readiness script as `llm-runner`: pytest imports, two smoke tests
  pass, and a deliberately triggered `UnboundLocalError` is detected by pytest.
- Ran an end-to-end Qwen3-Coder 30B / OpenCode smoke in a disposable runner
  workspace.  With no source edits permitted, Qwen invoked exactly
  `/srv/llm-runner/venv/bin/python -m pytest -q .` and received `2 passed`.

## Known controller issue

The tracked launcher source is not automatically present at the remote checkout
path.  The stable GMKtec launcher currently lives at
`/home/cdc/llm/ab/llama-qwen3-coder-30b.sh`; the running localhost-only Qwen
process used that same GGUF at 64K context during this non-timing smoke.
Future task controllers must either invoke this verified remote launcher or
explicitly sync a versioned launcher before starting a server.  They must never
assume a controller-side repository path exists on GMKtec.
