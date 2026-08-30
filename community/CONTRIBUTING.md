# Contributing reproducible local-model results

Contributions are welcome. A result should
be treated as diagnostic evidence, not as a leaderboard claim, unless it is
independently reproducible.

## Required metadata

- Hardware model, memory capacity, firmware/power mode, and operating system.
- GPU device and driver/backend versions.
- Serving backend, exact version or commit, and complete non-secret command.
- Exact model identifier, file digest, quantization, and chat template.
- Requested and independently observed effective context.
- Tool schema, system prompt hash, task packet hash, sampling parameters, and
  generation limit.
- Start/end timestamps, wall time, stop reason, prompt/decode counts and rates,
  peak resource observation, and raw parser outcome.
- Number of total, unique, duplicate, invalid, and rejected tool calls.
- Test command and machine-readable test result.

## Repetition and comparisons

- Run at least three repetitions for comparative claims.
- Change one relevant variable at a time.
- Backend comparisons must use equivalent model weights, quantization, template,
  prompt, tools, context, and generation settings.
- Timeouts and serving failures are results and must not be silently retried.
- Mark contaminated timings rather than deleting them.

## Redaction and safety

Do not submit credentials, tokens, OAuth/profile data, private source code,
personal paths, private hostnames, account identifiers, or proprietary task
packets. Inspect raw transcripts before submission. Tool execution must be
confined to a disposable task directory and must not expose network access or
production data unless the test explicitly documents a safe boundary.

## Translation

Translations should link to the exact source revision. Preserve model names,
hashes, commands, units, and error strings. If a technical phrase has no stable
translation, retain the original term alongside the translated explanation.
