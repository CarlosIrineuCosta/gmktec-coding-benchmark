# Next steps — local model benchmark

Last updated: 2026-08-16.  This is the restart checklist.  Read it before
launching another model task.

## Current position

- The benchmark repository is private: `CarlosIrineuCosta/gmktec-coding-benchmark`.
- The first real Historical pair is frozen in
  `docs/reports/2026-08-16-suite-v2-historical-pair.md`.
- No patch has been promoted to The Floor or any canonical repository.
- **Do not run Codex Sol on another benchmark task.**  Its Historical result is
  the established control/baseline for this phase.
- The canonical Floor checkout remains dirty and must not be used as a model
  worktree.  The Sol candidate is an isolated snapshot under
  `data/private/runs/suitev2-historical-codex-sol/worktree`; it is based on
  Floor commit `87a75208`, not the current canonical checkout.

## Non-negotiable controller rules

1. Prepare a fresh isolated worktree before the model sees a task.
2. Run the controller readiness gate **as the exact Unix user that will run the
   harness**.  A successful check as `cdc` does not prove readiness for
   `llm-runner`.
3. Record the green gate before asking the model for `READY` / `MISSING`.
4. The model preflight must state the task summary and available commands.  It
   may answer only `READY` or `MISSING: <precise item>`; do not ask it to read
   files while forbidding tool use.
5. The implementation prompt must name the exact Python test command.  For
   GMKtec local runner tasks use:

   ```text
   /srv/llm-runner/venv/bin/python -m pytest
   ```

6. If the readiness gate, model preflight, model-server canary, or test command
   fails, stop that run and record the failure.  Do not score it as an ordinary
   coding failure and do not substitute a different interpreter silently.
7. Preserve raw transcripts/results under `data/private/`; publish only
   sanitized reports under `docs/` or `community/`.

## Tests that now exist

### Common Python readiness smoke

Tracked canary: `canaries/python-test-readiness/`.

- `test_pytest_runs_a_passing_test`: proves the selected interpreter can execute
  pytest normally.
- `test_pytest_surfaces_unboundlocalerror`: deliberately invokes the same class
  of `UnboundLocalError` that invalidated the first Qwen Historical patch.  The
  test passes only when pytest catches that runtime error correctly.

Gate script:

```text
deploy/gmktec/verify-python-test-env.sh [canary-directory]
```

It checks that the exact interpreter exists, imports pytest, compiles the smoke
modules, and runs both tests.  It fails closed.

### Verified results

| Test | Exact executor | Result |
| --- | --- | --- |
| Controller smoke | `/usr/bin/python3` on controller | `2 passed` |
| Actual GMKtec runner smoke | `llm-runner`, `/srv/llm-runner/venv/bin/python` | `2 passed` |
| Qwen/OpenCode end-to-end smoke | Qwen3-Coder 30B through OpenCode as `llm-runner` | Model ran exactly `/srv/llm-runner/venv/bin/python -m pytest -q .`; `2 passed`; no edits |
| Historical focused suite — Qwen first attempt | independent replay on controller | `5 passed, 36 failed`; invalid patch, do not promote |
| Historical focused suite — Sol candidate | independent replay on controller | `71 passed` |
| Historical broad suite — Sol candidate | candidate then pristine baseline comparison | `745 passed, 5 baseline-only failures`; exact-node deselection: `745 passed, 5 deselected` |

The first Qwen Historical run could not run tests because `pytest` was missing
from `llm-runner`.  That environment error is corrected.  Its independent
functional failure still stands: it shadowed and then called
`existing_attempts`, producing an immediate `UnboundLocalError`.

## Installation/configuration now present

### GMKtec `llm-runner`

- Account: `llm-runner`, UID/GID 1001, no sudo/supplemental groups.
- Worktrees: `/srv/llm-runner/workspaces/<run>`.
- OpenCode: `/srv/llm-runner/.opencode/bin/opencode`, verified version 1.18.18.
- Python test environment: `/srv/llm-runner/venv`, with `pytest==9.1.1`.
- Runner bootstrap: `deploy/gmktec/bootstrap-llm-runner-pytest.sh`.
- Remote deployed copies of the readiness assets:
  `/srv/llm-runner/profile/benchmark-readiness/`.

The runner venv is the only supported Python environment for local benchmark
tasks.  Do not use the older `cdc`-owned canary venv as proof that a runner can
test.

### Serving plane

- Canonical local coding serve plane remains `llama-server`, not Ollama.
- Qwen3-Coder 30B served successfully through OpenCode using its localhost
  OpenAI-compatible endpoint.
- The currently observed active Qwen server is a localhost-only process on
  port 8081 using the exact Qwen GGUF at 64K context.  It was not stopped,
  because it may serve the owner's chat workflow.
- The verified GMKtec launcher path is:

  ```text
  /home/cdc/llm/ab/llama-qwen3-coder-30b.sh
  ```

  Do not assume the controller-side repository launcher path exists remotely.
  Before a timing run, either use the verified remote launcher or explicitly
  sync a versioned copy, then record its command, PID, `/props`, and `/metrics`.

## What is still missing

### Qualified now

- **Qwen3-Coder 30B + OpenCode + llama-server** is ready for one new isolated
  local coding task.  Before it receives that task: create a fresh worktree,
  rerun the runner gate, verify the server model/template/context, and give the
  model the exact pytest command in the prompt.

### Not qualified yet

- **Qwen Code + Qwen3-Coder 30B:** Qwen Code is not installed for
  `llm-runner`.  Install/configure it in that account's profile, then run the
  same end-to-end two-test smoke.  Do not borrow `cdc`'s profile or credentials.
- **GPT-OSS 120B:** model is present in Ollama inventory, but there is no frozen
  llama-server GGUF/template/endpoint canary.  Qualify serving and one bounded
  test invocation before a coding task.
- **GLM-4.6V Flash:** model is present, but no llama-server GGUF/template or
  one-tool-call canary is qualified.  First prove one bounded command/test
  response, then decide whether it is usable as an agent.
- **Qwen3-Coder Next and Gemma4:** base runner is ready, but each needs its own
  exact model blob, chat template, context setting, and model-server canary.
- **Kimi K3:** CLI is installed under `cdc`, but no dedicated benchmark
  `KIMI_CODE_HOME` has been verified in this repository.  Do not copy legacy
  credentials or Tessera `.env` routes.  Verify dedicated profile/OAuth, run the
  host Python readiness gate, then run the end-to-end two-test smoke before its
  small real task.
- **Z.AI GLM-5.3 via Claude Code:** Claude Code is installed, but its isolated
  benchmark profile, endpoint, and end-to-end pytest smoke are not recorded as
  green.  Verify them before a task.
- **Codex Terra:** host Python smoke is green, but no further Codex task is
  needed until the next model-selection decision.  **Codex Sol must not be run
  again.**

## Recommended next sequence (do not start automatically)

1. Review the Sol Historical patch against the historical source snapshot.  It
   is a candidate only; do not apply it to the dirty canonical Floor checkout.
2. Rerun the Historical task once with the now-qualified Qwen/OpenCode pair in
   a fresh snapshot, with the explicit test interpreter in its prompt.  This is
   the only local rerun currently justified.
3. Install/qualify Qwen Code for `llm-runner` and compare it using the same
   two-test end-to-end smoke before assigning it a real task.
4. Perform small server/tool canaries for GPT-OSS 120B and GLM-4.6V Flash;
   neither should receive the Historical task first.
5. Qualify Kimi K3 and GLM-5.3 profiles before spending external quota.
6. Only after per-pair qualification should the team select a model for the
   independent Research or Daily Ops task.  Do not start Whisper installation
   or production integration during this benchmark phase.

## Pointers

- Harness contract: `docs/architecture/2026-08-16-harness-readiness-contract.md`
- Local remediation evidence: `docs/reports/2026-08-16-local-runner-readiness-remediation.md`
- First Historical pair: `docs/reports/2026-08-16-suite-v2-historical-pair.md`
- First local Qwen failure transcript/results: `data/private/runs/suitev2-historical-opencode-qwen/`
- Sol candidate: `data/private/runs/suitev2-historical-codex-sol/worktree/`
