# Task: stop Delivery Supervisor replay effects

Work only in this snapshot. Do not inspect other repositories, git remotes, or
network resources. Implement the repair and tests; do not deploy or mutate a
live Hub.

The Delivery Supervisor repeatedly injected already completed Work Orders.
Two deterministic `tmux_delivery_sent` event IDs had been appended 146 and 232
times. Repair the four interacting defects:

1. Evidence must bind to the exact `source_event_id` and audience/endpoint leg;
   correlation-wide refs are diagnostic only.
2. Select latest attempts/receipts deterministically by parsed timestamp and
   stable event-ID tie-breaker, independent of hash iteration.
3. Exact claim/start consumes the original command delivery and exact terminal
   evidence terminates it; another Work Order sharing a correlation cannot.
4. Add a pre-send effect fence keyed by source event, audience, target session
   generation, and prompt hash. A committed successful effect cannot submit or
   append again after replay/restart.

Allow an initial failure plus at most one policy-eligible retry. Never retry a
successful transport merely because endpoint consumption is pending. Preserve
append-only evidence, fairness, endpoint receipts, alarms, and authority
boundaries. Add regression coverage for repeated sent IDs, multiple
`PYTHONHASHSEED` values, cross-source correlation contamination, exact
claim/start/terminal suppression, restart fencing, bounded failure retry,
changed session generations, blocked panes, missing endpoints, and callbacks.

Run relevant tests and `git diff --check`. Do not write reports outside this
worktree.
