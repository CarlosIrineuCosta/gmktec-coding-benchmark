# GMKtec local backend A/B profile

This directory holds the reversible GMKtec configuration for comparing the
existing Ollama route to `llama-server`. It is not a Floor provider integration.

## What is configured

- `llama-qwen3-coder-30b.sh` starts one localhost-only `llama-server` process
  on port 8081.
- It reads the exact Qwen GGUF payload already owned by Ollama. It does not copy,
  download, mutate, or delete model data.
- `qwen3-coder-30b-manifest.json` pins the blob SHA-256, build commit, intended
  transport, and parser-related Ollama metadata.
- The profile enables Jinja chat parsing and Prometheus metrics, but never
  enables llama.cpp built-in tools or agent mode.

## Deliberately not configured

- No systemd service or persistent resident process.
- No Tailscale/LAN binding; the server is `127.0.0.1` only.
- No Floor route or provider-code change.
- No driver, kernel, Ollama configuration, or model-file change.
- No GPT-OSS or GLM service.

## Controlled run procedure

Run only after the common canary packet is frozen. Execute the harness on
GMKtec, so both endpoints remain local:

```text
Ollama:       http://127.0.0.1:11434/v1
llama-server: http://127.0.0.1:8081/v1
```

For each context in 8192, 16384, and 32768 (advance only after three successful
prior runs), start `llama-qwen3-coder-30b.sh` with `LLAMA_CTX_SIZE` set to that
value, run the three repetitions, collect `/health`, `/props`, `/metrics`, and
host resource samples, then stop the process before the next condition.

The same Qwen blob, temperature, generation cap, tool schema, prompt, and
strict one-tool-call executor must be used with Ollama. A multiple or malformed
tool call is a recorded contract failure, not a retry.
