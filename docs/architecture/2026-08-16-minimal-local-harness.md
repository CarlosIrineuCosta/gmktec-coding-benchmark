# Minimal local harness: bounded qualification profile

This profile is a deliberately small comparison point for Qwen Code, not a
replacement for Floor. It runs as the restricted `llm-runner` account against
a loopback-only llama-server process.

Each task is fully specified before inference. The preflight phase accepts only
an exact `READY` response or a `MISSING` response with a specific need. The
execution phase offers one generic `repository_action` function. It permits
only reads of the two supplied files, an overwrite of `module.py`, and the
explicit standard-library test command. A second tool call in one turn, an
unknown action, a path escape, or a response that stops before a tool action is
a recorded failure, not something the harness repairs.

This first pass uses three disposable two-file Python canaries at 64K context.
It has no hidden tests, network access, package installation, credentials,
canonical repository access, or production data.
