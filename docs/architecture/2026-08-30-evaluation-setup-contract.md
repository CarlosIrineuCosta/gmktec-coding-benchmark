# 2026-08-30 evaluation setup contract

**Status:** accepted setup contract; pilot execution remains blocked pending
owner selection.

## Prepared components

- `benchmark.supervised_eval.inventory` captures read-only machine/runtime and
  exact model-file metadata. It hashes only when `--hash-models` is selected.
- `benchmark.supervised_eval.lifecycle` owns a disposable loopback server's
  launch, health check, and cleanup. A caller supplies the exact server command
  and exact GGUF; it never selects a model or changes the persistent Studio
  service.
- `benchmark.supervised_eval.harness` exposes a small OpenAI-compatible tool
  contract restricted to a disposable worktree. `session` writes full model and
  tool trajectories only to the private evidence root.
- `EvidenceStore` creates append-only per-run evidence. It separates observed
  events, interventions, metrics, acceptance, and compact summary output.
- `LoopDetector` surfaces repeated unchanged action/state pairs for Codex to
  judge. It never ends a run or sends an intervention autonomously.

## Supervision and terminal record

Codex records a decision at each approximately five-minute checkpoint during a
real run. I0–I3 interventions are written separately; I4 is rejected by the
evidence API as forbidden benchmark assistance. Terminal classifications keep
model, server, harness, infrastructure, and operator outcomes distinct.

## Task preparation

- The gallery packet and Playwright contract test observable behavior without
  prescribing implementation. Its image corpus manifest must be instantiated
  in the private fixture surface before the pilot.
- The code-review fixture/gold lives only under `data/private/code-review/`.
  Its public packet describes output/scoring but not defects or gold labels.
- The translation packet intentionally awaits the owner-supplied English source.

## Pilot guard

`tasks/local-model-evaluation/pilot.json` contains two null model slots. The
`selected_pilot_models` guard refuses execution until the Owner names exactly
two model identities. Setup tests use fake responses and mocked lifecycle
primitives; they do not start candidate inference.

## Required pilot preflight

Before the first real candidate turn, capture a fresh manifest on GMKtec as
`cdc`, including the exact artifact repository, snapshot/revision, filename,
bytes, SHA-256 where practical, server command, native template, context,
reasoning configuration, sampling, tool contract, and effective endpoint.
Record any deviation from the persistent Studio management service as a
disposable run-local lifecycle choice.
