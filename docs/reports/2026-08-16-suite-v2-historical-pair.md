# Suite v2 Historical pair — first real execution

Status: frozen for review; no patch promoted.

## Common conditions

- Snapshot: `87a75208dd46796fde2b3b687403fdb802e6934e` from The Floor.
- Task packet: `tasks/historical/PACKET.md`, with `tasks/historical/SUITE_V2.md`.
- Both candidates used fresh, isolated copies of the snapshot.  Neither could
  reach canonical repositories, network services, credentials, or live Floor
  state.
- The original focused baseline was `40 passed, 1 failed`.  The existing
  failure was `test_later_endpoint_consumption_outranks_prior_tmux_transport`.

## Qwen3-Coder 30B via OpenCode / llama-server

- Run duration: 7.3 minutes from first execution event to normal stop.
- The agent completed a source patch and a prose `REGRESSION_TESTS.md`, but did
  not add executable regression tests.
- Its restricted GMKtec runner did not have `pytest`, so it could not perform
  the requested test cycle.  This is an environment-provisioning defect in
  this run, and must be fixed before another scored OpenCode local run.
- Independent replay of the captured patch in the prepared test environment:
  `5 passed, 36 failed` in the focused suite.  The root cause was an immediate
  `UnboundLocalError`: a local assignment shadows the `existing_attempts`
  callable and then attempts to call it.
- The patch also did not implement the specified effect key coherently; its
  claims in the summary were materially ahead of the code and tests.

Result: **functional failure; do not promote.**  This is not evidence that
Qwen is unusable: it is evidence that this concrete harness/run needs pytest
available and still produced an invalid repair once independently checked.

## Codex Sol High

- Execution began after the successful preflight and completed in about
  24.8 minutes (preflight log completion at 18:42:36 BRT; execution completion
  at 19:07:25 BRT).
- It diagnosed the visible baseline defect as a wall-clock routing issue:
  replayed historical acknowledgements were appended to the current month
  rather than the event's month.
- It introduced a dedicated deterministic replay helper, applied exact-source
  and endpoint-leg handling to the reducer/sender, added a narrowly validated
  historical acknowledgement timestamp path, and added executable regression
  tests.
- Independent final replay: `71 passed` across the delivery-focused suites;
  `git diff --check` passed.
- Full suite: `745 passed, 5 failed`.  The five failures reproduced on an
  archived pristine `HEAD`; they are baseline fixture/date and stale
  role/owner failures.  With those exact five nodes deselected:
  `745 passed, 5 deselected`.

Result: **candidate for manual code review only.**  The diff is substantial
(roughly 600 added lines across sender, reducer, broker, and tests), so the
next decision is not automatic promotion; it needs an exact-scope review and
comparison against the historical human repair.

## Harness findings

1. The v2 preflight/execute separation worked as a controller protocol, but
   its literal “no tool use” preflight wording conflicted with a prompt that
   asked agents to read packet files.  Embed the minimum task summary in the
   preflight prompt next time.
2. A local coding harness must ship the test runner and the project test
   dependencies.  Absence of `pytest` is controller setup failure, not a model
   quality signal.
3. The Sol result supports longer allowance for careful coding systems: it
   used about 25 minutes, including baseline investigation, new tests, focused
   validation, full-suite validation, and baseline reproduction.
4. The first local result does not yet qualify OpenCode/Qwen for this task;
   repair the runner environment and retry a small module under the same
   observed llama-server route before running another large local task.
