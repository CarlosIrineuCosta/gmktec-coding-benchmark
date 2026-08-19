# GMKtec Coding-Benchmark Coordinator Charter

**Coordinator session:** `c-coding-benchmark`  
**Working root:** `/home/cdc/Storage/projects/coding-benchmark`  
**Authority:** direct Charles Owner instruction, 2026-08-18  
**Status:** temporary bounded exception while Floor communications/recovery are impaired

## Mission

Coordinate and execute the GMKtec local-model evaluation. Preserve useful
waypoints, produce reproducible evidence, and prepare public evaluation
methodology suitable for independent model and Unsloth review.

## Public evaluation scope

The following are public-by-default and may be edited, tested, committed, and
published in this repository:

- benchmark harnesses, task packets, scoring/validation code, and methodology;
- non-secret model/run metadata, timings, failure classifications, and reports;
- OSS browser artifacts, including the volcano simulation and raycaster/
  Rayblaster-style tests;
- reproducible prompts and non-secret command parameters.

## Strict private-project boundary

Never read, copy, paste, transmit, commit, or expose source, tests, documents,
assets, credentials, or runtime data from The Floor, TesseraFold, or any other
internal project as part of a public benchmark.

When Charles explicitly authorizes a test against internal code:

1. Materialize only the named, non-secret minimal fixture under
   `.local/experiments/private-fixtures/<run-id>/`.
2. Keep it Git-ignored and local-only.
3. State exactly which files were materialized and which were excluded.
4. Do not send it to an external model unless Charles separately authorizes
   that precise fixture and provider route.
5. Never promote model-generated patches from that fixture into an internal
   project; they require an independently reviewed implementation request.

The existing local archive root is `.local/experiments/`. Provider credentials,
OAuth state, API keys, and Kimi/Claude profile homes are never copied there.

## GMKtec host boundary

GMKtec is persistent Linux infrastructure, not a disposable OS image. It has
no production service in scope at present. Do not upgrade/reinstall the OS,
drivers, packages, or model runtime; do not change networking, storage, or
system services; and do not perform destructive cleanup without a new explicit
Owner instruction. Disposable work belongs only in benchmark-local worktrees
and `.local/experiments/`.

## Operating discipline

- Read this charter and the applicable Floor protocol/role guidance before
  starting a new campaign.
- Treat direct Charles instructions as the approval basis for this bounded
  coordinator. Roles constrain autonomous agent behavior; they do not erase a
  specific Owner instruction.
- Preserve dirty worktrees and stage only intentional benchmark changes.
- One loaded local model at a time; record the actual invocation and request
  parameters.
- Keep simulations and games available for Charles when he asks to inspect
  them; do not terminate their preview servers merely to clean a process list.
- Report evidence and real blockers, not speculative recommendations.

## Coordinator outputs

- tracked public methodology, reports, and OSS evaluation code in this repo;
- ignored local artifacts under `.local/experiments/`;
- a precise final result and any required implementation request for separate
  internal-project work.
