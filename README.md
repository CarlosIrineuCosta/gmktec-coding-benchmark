# Nine-System Coding Benchmark

> **2026-08-30 campaign notice:** the text below records the retired August 16
> coding matrix. New GMKtec work is governed by
> `docs/architecture/2026-08-30-supervised-unsloth-evaluation.md` and
> `docs/handoffs/2026-08-30-local-model-evaluation-coordinator.md`; it runs as
> `cdc` through Unsloth/llama.cpp, not the retired `llm-runner` path.

Reproducible benchmark for five GMKtec Ollama models, Z.AI GLM-5.3
through Claude Code, Kimi K3 through Kimi Code, and Codex Terra/Sol controls.
Each run receives a fresh isolated worktree, one packet hash, no native web
tools, and a 30-minute hard timeout. Canonical repositories are read only.

The main 64K matrix may use two independent lanes: exactly one GMKtec model and
exactly one external coding system at a time. Runs remain sequential within
each lane. Host-side load or unexpected GMKtec model residency must be recorded
as timing contamination; it does not invalidate functional scoring. The
32K/64K/96K/128K context ladder is explicitly deferred and is not part of this
run.

## Public repository boundary

This GitHub repository is intentionally public. Tracked material must remain
sanitizable: public methodology, evaluation code, task packets, reports, and
open-source browser artifacts are allowed; credentials, private-project
material, hidden gold data, raw transcripts, model caches, and local run state
are not. Keep the latter under the ignored `data/private/` boundary.

```bash
python3 -m benchmark.preflight
python3 -m benchmark.run_matrix --context 65536
python3 -m benchmark.score
```

Readable project material belongs under [`docs/`](docs/README.md). Generated
evidence, candidate worktrees, hidden tests, and provider profiles belong under
the gitignored `data/private/` boundary. A timeout is terminal and is never
retried. Use `--dry-run` to print the 27-run matrix without invoking a model.
