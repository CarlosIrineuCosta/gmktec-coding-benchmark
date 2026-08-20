# Vitorianas Macabras search matrix

**Date:** 2026-08-19 to 2026-08-20  
**Backend:** isolated Unsloth Studio on GMKtec, loopback-only, 64K context  
**Status:** complete; all 12 cells reached a durable terminal result.

This is a behavioral matrix, not a pass/fail benchmark. Search-budget excess,
timeout, context exhaustion, and unsupported reasoning-mode requests are
recorded as observed model/backend behavior.

## Results

| Cell | Terminal result | Elapsed (s) | Executed searches | Note |
| --- | --- | ---: | ---: | --- |
| Q35-9-OFF | completed | 146.070 | — | completed answer captured |
| Q35-9-LOW | search-budget violation | 507.334 | 43 | overthought beyond the 20-search budget |
| Q38-UD-OFF | search-budget violation | 817.354 | 31 | overthought beyond the 20-search budget |
| Q38-UD-LOW | timed out | 1213.145 | 20 | reached the cell cap |
| Q38-UD-HIGH | completed | 880.470 | 17 | completed answer captured |
| Q38-Q6-OFF | completed | 318.515 | 19 | completed answer captured |
| Q38-Q6-LOW | timed out | 1214.025 | 8 | did not complete before the cap |
| Q38-Q6-HIGH | failed | 1168.466 | 19 | context exhaustion: 77,411 > 65,536 tokens |
| GLM-OFF | completed | 221.484 | 0 | rerun with required `min-p 0.01` |
| GLM-ON | failed | 8.952 | 0 | Studio rejected `reasoning_effort=enabled` |
| GEMMA-OFF | completed | 41.326 | 6 | rerun with Studio model-detected defaults |
| GEMMA-ON | failed | 7.052 | 0 | Studio rejected `reasoning_effort=enabled` |

## Public evidence

Sanitized machine-readable artifacts are tracked in
[`community/artifacts/vitorianas-search-matrix-20260819/`](../../community/artifacts/vitorianas-search-matrix-20260819/):

- `download-manifest.json`, exact model/revision/quant checksums;
- `matrix-results.csv` and the runner summary;
- each cell's request, model metadata, terminal record, response where safe,
  and failure record where applicable.

Four raw model-output files are deliberately not included because a model
emitted an Unsloth API-key-shaped value into its answer. The runtime Studio
logs are also excluded: they contain generated API-key lines. Those files
remain only in the disposable, access-controlled runtime directory and are
not benchmark publication material.

The prompt, methodology, backend boundary, and original cell matrix are in
[`docs/handoffs/2026-08-19-vitorianas-search-matrix-coordinator.md`](../handoffs/2026-08-19-vitorianas-search-matrix-coordinator.md).
