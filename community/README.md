# Community publication area

This directory is the deliberately sanitized boundary for material published
from the public GMKtec coding benchmark repository.

It contains no provider profiles, credentials, private project snapshots,
hidden acceptance tests, candidate worktrees, or unredacted model transcripts.
Moving a file into this directory does **not** automatically approve it for
publication: every release still requires a secret, privacy, provenance, and
license review.

## Current contents

- `reports/2026-08-16-initial-backend-findings.md`: sanitized initial findings
  from the Ollama tool-loop canaries.
- `schemas/run-result.schema.json`: proposed portable record format for future
  community results.
- `CONTRIBUTING.md`: minimum evidence and redaction requirements.

## Future multilingual structure

English is the source version for now. If translations are added, preserve the
source evidence and technical identifiers exactly and use language-specific
paths such as:

```text
community/docs/en/
community/docs/pt-BR/
```

Translations should state the source revision they correspond to. Benchmark
data, hashes, commands, model identifiers, and error messages must not be
silently localized or altered.

## Public-repository boundary

The repository is public by owner decision. Publication remains a per-file
review: only sanitized, non-secret material may be committed here.
