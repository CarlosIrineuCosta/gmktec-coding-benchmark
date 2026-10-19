# RTX 3080 Ti versus GMKtec: first comparable run

This is a serving and coding-review probe, not the full Floor benchmark. It
reuses the local OpenAI-compatible interface and keeps all generated responses
in one private JSON file. Run the same model artifact and prompt on the GMKtec
when comparing hardware. Do not compare this 9B model's speed with a different
30B model and attribute the difference to the machines.

## Windows 11, one RTX 3080 Ti (12 GB)

1. Get the **CUDA** Windows build of `llama.cpp` from its release page:
   <https://github.com/ggml-org/llama.cpp/releases>. Check that the extracted
   build has `llama-server.exe` and CUDA libraries. In PowerShell, in that
   directory, inspect `./llama-server.exe --list-devices`. Use the exact device
   identifier reported for the RTX 3080 Ti, not the 3070 Ti. If the CUDA build
   needs a separate CUDA runtime archive, use the matching release's asset.
2. Start with the text-only Qwen3.5-9B `Q4_K_M` GGUF (5.68 GB):
   <https://huggingface.co/unsloth/Qwen3.5-9B-GGUF>. The `Q6_K` file is
   7.46 GB and makes a useful second quantization run once the first works.
   Download the exact file to a model folder, or use llama.cpp `-hf` with the
   repository and quantization selector. Record its SHA-256 with
   `Get-FileHash -Algorithm SHA256`.
3. In a PowerShell window, with the path adjusted to your downloaded file:

   ```powershell
   ./llama-server.exe -m 'C:\Models\Qwen3.5-9B-Q4_K_M.gguf' --device CUDA0 -ngl all -c 8192 -np 1 --host 127.0.0.1 --port 18080 --metrics --no-mmproj
   ```

   Replace `CUDA0` with the device ID shown by `--list-devices`. Read startup
   output: it must report all model layers on the 3080 Ti and the effective
   context. If it offloads layers to CPU, measure that as a separate condition.
   Use `nvidia-smi` to record occupied VRAM; close other GPU-heavy software
   if it interferes. Keep the server bound to loopback.

4. In another PowerShell window, with Python 3 installed:

   ```powershell
   python .\endpoint_probe.py --base-url http://127.0.0.1:18080/v1 --output .\results\3080ti-q4.json
   ```

   It performs one warmup and three recorded runs of a short code review and a
   repetitive copy prompt. Add a real, sanitized task prompt via
   `--prompt-file .\my-coding-prompt.txt`. Do not use a hidden answer or a
   canonical Floor checkout as candidate work material. The JSON stores
   model output, token usage if served, first-token latency, wall time and
   GPU snapshots. If the endpoint omits usage, token rates remain `null`.

## GMKtec control

Use the existing `cdc` Unsloth/llama.cpp stack to launch a *disposable* local
server for the **same GGUF** and 8192 context, on an unused loopback port. Keep
Studio on 18888 available. Capture exact model file hash, llama.cpp build,
Vulkan/RADV version, host power mode, and server launch command. Run this same
script against its `/v1` endpoint and save a distinct result. If running the
script from the Windows machine, the GMKtec endpoint must be reached through
an SSH tunnel to the loopback port; do not rebind the server to the LAN merely
for a test. Alternatively, copy the script to the GMKtec and run it locally.

The first-token value includes queueing and prompt processing. The approximate
decode rate divides all reported completion tokens by elapsed time since the
first visible token; reasoning tokens may not appear as visible text. Compare
wall time and reported usage first, then inspect outputs. The copy case probes
speculation-friendly repetition; the coding case probes a distinct workload.
Neither automatically scores code-review correctness. Run the repository's
accepted, isolated gallery and review tasks after the endpoint and tool-call
canary works on the new server/model pair. The August 30 architecture replaces
the older Ollama-first README and 30-minute universal timeout.

HyperQwen's one-card recipe requires 24 GB and a specialized Qwen3.8-27B
checkpoint. This 12 GB probe deliberately uses llama.cpp CUDA and Qwen3.5-9B;
it does not claim HyperQwen's DFlash2 speedups transfer to this model.
