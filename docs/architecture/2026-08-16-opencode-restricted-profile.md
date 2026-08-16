# OpenCode restricted qualification profile

OpenCode is evaluated as a separate coding harness using the same restricted
`llm-runner` Unix account and loopback-only llama-server endpoint as the
minimal local harness. The Unix account is the host boundary; OpenCode's
permissions are a second layer for reproducibility and scope control.

The project-local profile defaults every permission to deny. It allows workspace
reads (except `.env` files), edits only to paths ending in `module.py`, and the exact command
`python3 test_canary.py`. External directories, web tools, subagents, skills,
LSP, questions, and loop recovery are denied. OpenCode runs with `--pure` and
an isolated XDG configuration/data/cache profile, so no user-installed plugins
or credentials are available.

This is a compatibility qualification, not a claim that OpenCode has a
container-quality sandbox. Any real repository use remains gated by the
restricted Unix account and a dedicated worktree.

The companion `*-practical.json` profile is deliberately less narrow for one
compatibility canary: ordinary workspace read/edit/shell tools are enabled
while external directories, web tools, subagents, and skills remain denied.
It relies on the same restricted Unix account for host containment.
