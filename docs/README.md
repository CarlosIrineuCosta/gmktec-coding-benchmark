# Benchmark documentation

This directory is the tracked, public, readable surface of the benchmark.

- `reports/`: verified findings and comparison records.
- `handoffs/`: bounded continuity notes for the next operator or reviewer.
- `architecture/`: stable serving and harness decisions when they are adopted.
- `intake/`: raw external source material, kept distinct from accepted state.

Source code remains in `benchmark/`, small public canaries in `canaries/`,
deployment launch assets in `deploy/`, and task packets in `tasks/`.

Generated run trees, unredacted transcripts, hidden tests, results JSON, and
provider/OAuth profiles are operational data, not documents. They are stored
under the gitignored `data/private/` boundary. Sanitized material intended for
external collaboration remains under `community/`. Raw external-LLM source
material remains under `docs/intake/` until it is accepted.
