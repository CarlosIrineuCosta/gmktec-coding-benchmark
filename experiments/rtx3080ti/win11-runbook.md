# Win11 runbook: Qwen3.5 small-model probe on the RTX 3070 Ti (8 GB)

Audience: the operator agent (Codex) working directly on the Win11 machine.
Owner: Charles. Everything here runs locally; no API keys, no accounts, no
cloud services. Work in one folder, for example `C:\llm-probe\`. Do not skip
a phase's verification step.

Standing rails, in force for the whole runbook:

- Every server stays bound to `127.0.0.1`. Never rebind to the LAN.
- Record everything you do and observe into `C:\llm-probe\log.md` as you go.
- Raw outputs stay on this machine. Only the final summary table (Phase 7)
  goes back to the repository.
- Do not install Docker, WSL2, new drivers, or overclocking tools. Do not
  touch the GMKtec machine; the GMKtec control run is a separate, later task
  done by the owner's coordinator.
- If a step fails, record the exact error output and stop that branch; do
  not improvise a different toolchain. OOM in Phase 6 is expected data, not
  a failure of the runbook.

## Phase 0 - preflight and inventory

1. In PowerShell:

   ```powershell
   nvidia-smi
   python --version
   Get-PSDrive C
   [System.Environment]::OSVersion.VersionString
   ```

2. Record into `log.md`: GPU name as reported (must say RTX 3070 Ti),
   total VRAM (must be 8192 MiB), driver version, Python version (3.10+),
   free space on C: (need at least 20 GB), Windows build.
3. Stop conditions: another GPU is primary, VRAM is not 8192 MiB, Python is
   missing (install from python.org with "Add to PATH", nothing else), or
   free space is under 20 GB. Record and stop; do not proceed.

## Phase 1 - llama.cpp CUDA build

1. Download the latest Windows CUDA build of llama.cpp from
   <https://github.com/ggml-org/llama.cpp/releases>. The asset is named like
   `llama-bXXXX-bin-win-cuda-x64.zip`. If the same release ships a separate
   `cudart` archive for that build (for example
   `llama-bXXXX-bin-win-cuda-cudart-x64.zip`), download it into the same
   folder and extract both archives together.
2. Extract to `C:\llm-probe\llama\`. Verify:

   ```powershell
   cd C:\llm-probe\llama
   .\llama-server.exe --version
   .\llama-server.exe --list-devices
   ```

3. Record the build number and the exact device line for the 3070 Ti
   (typically `CUDA0`). If `--version` fails with a CUDA DLL error, the
   cudart archive was required and is missing; fix that before continuing.

## Phase 2 - model files

Download these three files into `C:\llm-probe\models\` (direct links, no
authentication needed). Verify each file's size in bytes against the table
with `(Get-Item <file>).Length`, then record its SHA-256 with
`Get-FileHash -Algorithm SHA256 <file>` into `log.md`.

| File | Exact URL | Bytes (must match) | Role |
| --- | --- | --- | --- |
| `Qwen3.5-4B-Q6_K.gguf` | `https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q6_K.gguf` | 3,525,956,768 | Primary run |
| `Qwen3.5-4B-Q8_0.gguf` | `https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q8_0.gguf` | 4,482,403,488 | Quality point |
| `Qwen3.5-9B-Q4_K_M.gguf` | `https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-Q4_K_M.gguf` | 5,680,522,464 | Stretch run (OOM allowed) |

Example:

```powershell
curl.exe -L -o C:\llm-probe\models\Qwen3.5-4B-Q6_K.gguf https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q6_K.gguf
(Get-Item C:\llm-probe\models\Qwen3.5-4B-Q6_K.gguf).Length
Get-FileHash -Algorithm SHA256 C:\llm-probe\models\Qwen3.5-4B-Q6_K.gguf
```

A byte size that does not match the table means a truncated download: delete
and retry. Do not proceed with a mismatched file.

Copy `endpoint_probe.py` from this repository into `C:\llm-probe\`.

## Phase 3 - serve the primary model (4B Q6_K, 8K context)

1. Launch, in its own PowerShell window:

   ```powershell
   cd C:\llm-probe\llama
   .\llama-server.exe -m C:\llm-probe\models\Qwen3.5-4B-Q6_K.gguf --device CUDA0 -ngl all -c 8192 -np 1 --host 127.0.0.1 --port 18080 --metrics --no-mmproj
   ```

   Replace `CUDA0` with the exact device id from Phase 1 if different.

2. Read the startup output and record in `log.md`: the line showing how many
   layers are offloaded (it must say all layers on the 3070 Ti), the
   effective context (8192), and the KV cache size. If any layer stays on
   CPU, stop, record, and report; do not measure that condition as Tier 0.
   If the build prints a KV/flash-attention warning, relaunch adding
   `-fa on` to the command and note it.
3. While the server is idle, snapshot VRAM:

   ```powershell
   nvidia-smi --query-gpu=name,memory.total,memory.used,power.draw,temperature.gpu --format=csv
   ```

## Phase 4 - probe the primary model

In a second PowerShell window:

```powershell
cd C:\llm-probe
python .\endpoint_probe.py --base-url http://127.0.0.1:18080/v1 --output .\results\3070ti-4b-q6k-8k.json
```

The script prints one progress line per run. It performs one warmup and
three recorded runs of the coding case and the copy case, and writes the
JSON incrementally. Then stop the server (Ctrl+C in its window) and
snapshot `nvidia-smi` once more; record both.

Repeat Phase 3 and Phase 4 for the second artifact with the same commands,
changing the model path and the output file:

- `Qwen3.5-4B-Q8_0.gguf` -> `.\results\3070ti-4b-q8-8k.json` (same `-c 8192`).

Optional, only if Charles has supplied a real sanitized coding prompt file:
add `--prompt-file <path>` to the probe call and note it in `log.md`.

## Phase 5 - quality gate (read the outputs)

Open each results JSON and judge the three recorded (non-warmup) runs of
each case:

- Coding case: the model must flag at least one of the two seeded defects in
  the `claim`/`deliver` source (a stale claim returned after the lease
  expires, or a send-then-record window that can replay an event) and
  propose a concrete fix. Zero real defects found is a fail, however fluent
  the prose.
- Copy case: the passage reproduced exactly, no preface.
- No run may end with `finish_reason` of `length` (truncation).

Record per model: pass/fail per case, which defects were found, and one
sentence of output-quality impression. This gate is read by you and later by
the owner; the script never auto-scores.

## Phase 6 - stretch run (9B Q4_K_M at 4K, OOM expected to be possible)

1. Launch the same command with the 9B file and a smaller context:

   ```powershell
   .\llama-server.exe -m C:\llm-probe\models\Qwen3.5-9B-Q4_K_M.gguf --device CUDA0 -ngl all -c 4096 -np 1 --host 127.0.0.1 --port 18080 --metrics --no-mmproj
   ```

2. If it fails to allocate (CUDA OOM during load or KV allocation), capture
   the exact error lines into `log.md`; that recorded failure is the datum
   that justifies (or not) moving Tier 1 to the 3080 Ti. Do not retry with
   ad-hoc quant changes beyond this one relaunch attempt: add `-fa on` once;
   if it still OOMs, stop.
3. If it loads, verify all layers on GPU as in Phase 3 and run the probe to
   `.\results\3070ti-9b-q4km-4k.json`, then apply Phase 5.

## Phase 7 - summary for the owner

Write `C:\llm-probe\summary.md` with this table filled from the JSONs (use
the median of the three recorded runs for timings; take
`completion_tokens_per_decode_second_approx` as the decode rate), plus the
quality-gate verdicts and any OOM evidence:

```markdown
| GPU | Model + quant | Context | TTFT (s) | Wall (s) | Decode tok/s | VRAM used (MiB) | Quality gate | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RTX 3070 Ti 8 GB | Qwen3.5-4B Q6_K | 8192 |  |  |  |  |  |  |
| RTX 3070 Ti 8 GB | Qwen3.5-4B Q8_0 | 8192 |  |  |  |  |  |  |
| RTX 3070 Ti 8 GB | Qwen3.5-9B Q4_K_M | 4096 |  |  |  |  |  |  |
```

Also record in `summary.md`: llama.cpp build number, driver version, SHA-256
of each model file, and whether `-fa on` was needed. This summary (and only
this summary) goes back to the repository; the owner will commit it.

## Phase 8 - upgrade tiers (do NOT execute now)

These are recorded so the next steps are unambiguous after the Tier 0
results:

- Tier 1, 3080 Ti (12 GB) board swap: rerun Phases 3-5 with the 9B Q4_K_M
  at `-c 8192` and then the 9B Q6_K (`Qwen3.5-9B-Q6_K.gguf`,
  7,458,301,152 bytes, same repository) at `-c 8192`. Use the device id the
  card reports; do not guess CUDA0.
- Tier 2, both boards (12 + 8 GB): llama.cpp row-split exploration only if
  the owner asks. HyperQwen stays out: its documented multi-GPU floor is
  24 GB total and its only checkpoint is Qwen3.8-27B.
- Tier 3, 3090 (24 GB): only now does HyperQwen apply - Docker Desktop with
  WSL2, `git clone https://github.com/syv-ai/HyperQwen`, `.env` from
  `.env.example`, `docker compose --profile single up -d`, first start
  pulls a 9.5 GB image and requantizes the model (~20 GB, once) into
  `./models`, serves on `127.0.0.1:18020`; on WSL2 set
  `VLLM_WSL2_ENABLE_PIN_MEMORY=1`. This phase needs its own runbook before
  it is executed.
