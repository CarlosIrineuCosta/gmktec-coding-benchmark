# Suite v2 task controller: Historical delivery replay

You are working in an isolated historical The Floor snapshot. This is a real
coding task, not a toy canary. The supplied `PACKET.md` is the complete product
requirement. The repository itself is the source map: inspect it before making
changes. Do not inspect network resources, sibling repositories, credentials,
or host configuration.

## Two phases

### Phase 1: preflight

Do not modify files, run tests, or invoke tools. Reply with exactly one of:

- `READY`
- `MISSING: <one precise item required to start>`

`PACKET.md`, the complete isolated repository, Python, pytest, git diff/status,
and ordinary repository inspection/editing are available. No network capability
or external source will be provided.

### Phase 2: implementation

After the controller says `EXECUTE`, inspect the relevant implementation and
existing tests, make the repair and regression tests, then run targeted tests
followed by the relevant broad tests. Use small coherent modules and checkpoint
with `git diff --check` and `git diff` before finishing.

## Boundary

Work only in this worktree. Do not deploy, send messages, start services, access
outside files, install packages, or change the benchmark controller. A failed
test is evidence to investigate, not a reason to claim completion.
