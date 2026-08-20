# Vitorianas Macabras search matrix

Cell timeout: 1200 seconds. Search-budget excesses are recorded as model behavior, not prevented.

| Cell | Status | Elapsed s | Executed web searches |
|---|---|---:|---:|
| Q35-9-OFF | completed | 146.07 |  |
| Q35-9-LOW | search_budget_violation | 507.334 | 43 |
| Q38-UD-OFF | search_budget_violation | 817.354 | 31 |
| Q38-UD-LOW | timed_out | 1213.145 | 20 |
| Q38-Q6-OFF | completed | 318.515 | 19 |
| Q38-Q6-LOW | timed_out | 1214.025 | 8 |
| GLM-OFF | completed | 221.484 | 0 |
| GLM-ON | failed | 8.952 | 0 |
| GEMMA-OFF | completed | 41.326 | 6 |
| GEMMA-ON | failed | 7.052 | 0 |
| Q38-UD-HIGH | completed | 880.47 | 17 |
| Q38-Q6-HIGH | failed | 1168.466 | 19 |

Per-cell raw requests, responses, terminal records, and Studio logs are retained under `runs/` and `logs/`.
