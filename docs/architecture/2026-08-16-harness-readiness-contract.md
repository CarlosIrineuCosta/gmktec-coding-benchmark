# Harness readiness contract

No model may receive an `EXECUTE` task turn until its pair-specific preflight
has passed.  A verbal `READY` from the model is necessary but not sufficient:
the controller must first record a green local readiness gate.

## Mandatory gate for every coding run

1. Fresh isolated worktree exists and the intended user can write it.
2. The exact harness executable and model endpoint/profile are available.
3. The selected Python interpreter can import `pytest`.
4. `py_compile` succeeds on the harmless smoke module.
5. The smoke suite passes, including a test that proves a runtime
   `UnboundLocalError` is surfaced by pytest.
6. Only then ask the model for `READY` / `MISSING`.  The preflight prompt must
   state the supplied task summary and the exact available commands; it must
   not require the model to use tools while also prohibiting tool use.

The reusable implementation is
`deploy/gmktec/verify-python-test-env.sh`.  Its companion bootstrap script is
`deploy/gmktec/bootstrap-llm-runner-pytest.sh`.

## Projected pairs and execution locations

| Pair | Harness / execution user | Workspace | Test interpreter | Readiness state |
| --- | --- | --- | --- | --- |
| Qwen3-Coder 30B | OpenCode 1.18.18 as `llm-runner` on GMKtec; localhost llama-server | `/srv/llm-runner/workspaces/<run>` | `/srv/llm-runner/venv/bin/python` | **Green:** actual user passed compile/pytest gate and Qwen executed the pinned 2-test command without edits. |
| Qwen3-Coder 30B | Qwen Code as `llm-runner` on GMKtec; localhost llama-server | `/srv/llm-runner/workspaces/<run>` | `/srv/llm-runner/venv/bin/python` | **Blocked:** Qwen Code is not installed for `llm-runner`; no task may run until its own profile and end-to-end smoke pass. |
| GPT-OSS 120B | Local harness as `llm-runner` on GMKtec; dedicated llama-server process | `/srv/llm-runner/workspaces/<run>` | `/srv/llm-runner/venv/bin/python` | Base Python gate is green; exact GGUF/template and model-server canary remain required. |
| GLM-4.6V Flash | Local harness as `llm-runner` on GMKtec; dedicated llama-server process | `/srv/llm-runner/workspaces/<run>` | `/srv/llm-runner/venv/bin/python` | Base Python gate is green; exact GGUF/template and one-tool model canary remain required. |
| Qwen3-Coder Next / Gemma4 | Local harness as `llm-runner` on GMKtec; dedicated llama-server process | `/srv/llm-runner/workspaces/<run>` | `/srv/llm-runner/venv/bin/python` | Base Python gate is green; each needs a separate model-server canary. |
| GLM-5.3 | Claude Code / Z.AI isolated profile as `cdc` | private benchmark worktree under `data/private/runs` | `/usr/bin/python3` | **Not yet verified:** profile auth/endpoint and end-to-end smoke required. |
| Kimi K3 | Kimi Code isolated `KIMI_CODE_HOME` as `cdc` | private benchmark worktree under `data/private/runs` | `/usr/bin/python3` | **Not yet verified:** no dedicated benchmark profile has been recorded; OAuth/profile and end-to-end smoke required. |
| Codex Terra / Sol | Codex native harness as `cdc` | private benchmark worktree under `data/private/runs` | `/usr/bin/python3` | Host Python gate is green.  Sol is baseline-only and will not receive another benchmark task. |

## Controller rule

The runner path is supplied in the implementation prompt, for example:

```text
Use /srv/llm-runner/venv/bin/python -m pytest for Python tests.
This interpreter and the supplied worktree passed the controller smoke gate.
If another required package or command is absent, reply MISSING before editing.
```

The model may use that interpreter for normal task tests.  The controller must
never infer test readiness from a chat canary, an unrelated host venv, or a
successful previous model run.
