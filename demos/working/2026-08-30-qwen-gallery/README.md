# Qwen gallery — retained working demo

This is the public, runnable gallery created by Qwen during the authorized
two-model pilot on 2026-08-30. It is retained because it is useful as an
inspectable design and implementation example, not because it passed every
benchmark acceptance check.

## Run it

Requires Node.js 24 or a compatible current Node.js runtime.

```bash
npm ci
npm run typecheck
npm run build
npm run preview -- --host 0.0.0.0 --port 4173
```

The public images and their source/license metadata are in
[`public/images.json`](public/images.json). No external asset request is
required by the application.

## Provenance

- Model: `unsloth/Qwen3.8-Flash-Next-GGUF`, revision
  `c8b5954a88c2775c546b92593eda40ea041d3176`.
- Exact quant: `UD-Q3_K_XL`, split across three GGUF shards.
- Server: local `llama-server` 0.3.0-dev build 10687, commit `92b19177a`;
  Vulkan; 64K context; `--gpu-layers 999 --flash-attn on --jinja --reasoning on
  --reasoning-effort xhigh --reasoning-preserve`.
- Request sampling: temperature 1.0, top-p 0.95, top-k 20, min-p 0, presence
  penalty 0, repeat penalty 1, maximum output 8192 tokens.
- Candidate model-turn elapsed time: 00:41:26.622 across 33 supervised turns.
- Exact initial prompt: [`PROMPT.md`](PROMPT.md). The canonical task contract
  is also retained unchanged as [`TASK.md`](TASK.md).

## Coordinator corrections

The coordinator did not edit the candidate application source and never used
forbidden I4 implementation assistance. The following logged supervisory
messages were supplied after observable stalls; they are reproduced verbatim.

1. I1 diagnostic:

   > Diagnostic: the current workspace still has no candidate implementation files after the completed task, test, manifest, image, and runtime inspection. Continue the existing task using the available tools; no task requirements have changed.

2. I2 criterion reminder:

   > Criterion reminder: completion requires the runnable gallery to satisfy the existing task contract and objective build/browser validation. Continue the task until those existing requirements are addressed; do not declare success solely from partial source modules.

3. I3 direction, first use:

   > Direction: prioritize the still-unfulfilled original task criteria over further refactoring of already-created modules. Attempt the remaining application work and the required objective validation, then address any resulting diagnostics with the available tools.

4. I3 direction, second use:

   > Direction: the validation files now exist. Run the current build and browser checks before further speculative edits, then use the observed command output to decide whether repair is required.

The later I0 message concerned only the host: Playwright could not launch
Chromium because shared browser libraries were absent. The coordinator did not
install system packages or change the generated source to work around it.

## Validation state

The candidate's own TypeScript typecheck and Vite production build passed.
Browser acceptance and screenshots were not produced because Chromium failed
before page execution on the GMKtec host. That result is recorded as
`infrastructure_blocked`, not as a model failure, in the pilot report:
[`docs/reports/2026-08-30-two-model-pilot.md`](../../../docs/reports/2026-08-30-two-model-pilot.md).

The app source promoted here is the retained candidate workspace. This README,
the exact prompt, and the working-demo catalog are operator documentation added
after the evaluation; they are not model-generated app source.
