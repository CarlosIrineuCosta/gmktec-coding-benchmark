# Nine-System Coding Benchmark

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

```bash
python3 -m benchmark.preflight
python3 -m benchmark.run_matrix --context 65536
python3 -m benchmark.score
```

Results and run worktrees are gitignored. A timeout is terminal and is never
retried. Use `--dry-run` to print the 27-run matrix without invoking a model.
