# GMKtec Ollama Context Precedence Lab

**Date:** 2026-08-17  
**Host:** `gmktec` (temporary direct-address diagnostic only; no address is
persisted)  
**Ollama:** 0.32.9  
**Status:** server and request context hierarchy measured; temporary-Modelfile
variant safely blocked by store-metadata behavior

## Method

Each probe started one secondary Ollama daemon on `127.0.0.1:11435`, used the
installed Qwen3-Coder 30B Q4_K_M artifact
(`06c1097efce043…89e90bca`), set Vulkan/RADV and one parallel request, sent a
fixed 14-token prompt with a four-token deterministic answer, captured that
daemon's `/api/ps`, and terminated the daemon before the next run.

The stable Ollama service on `0.0.0.0:11434` was never sent a request, stopped,
reloaded, or reconfigured. It was observed to retain its established 64K,
Vulkan/RADV, single-parallel configuration.

## Server-level results

| Daemon `OLLAMA_CONTEXT_LENGTH` | Observed `/api/ps` context | Result | Load duration |
| --- | ---: | --- | ---: |
| 8,192 | 8,192 | exact fixed reply | 3.53 s |
| 16,384 | 16,384 | exact fixed reply | 3.05 s |
| 32,768 | 32,768 | exact fixed reply | 3.28 s |
| 65,536 | 65,536 | exact fixed reply | 3.78 s |

The 8K runner log independently reported `n_ctx_slot = 8192`. Its short probe
measured about 142 prompt tokens/s and 115 decode tokens/s. The prompt is too
small to compare performance across contexts; these timings establish service
health and allocation only.

## Request-level precedence results

| Daemon default | Request `options.num_ctx` | Observed `/api/ps` context | Result |
| ---: | ---: | ---: | --- |
| 8,192 | 16,384 | 16,384 | exact fixed reply |
| 65,536 | 8,192 | 8,192 | exact fixed reply |

For this fresh-daemon/native-`/api/generate` configuration, `num_ctx` overrides
the configured daemon default in both tested directions. It also caused the
runner allocation to change rather than merely altering request metadata.

## Modelfile experiment

The planned temporary Modelfile used a fully separate temporary model store,
copied manifests, and production blobs through a read-only symlink. The
secondary daemon successfully discovered all seven installed models.

Ollama 0.32.9's supported `ollama create -f` path then attempted `chtimes` on a
source blob. That operation is forbidden through the read-only shared blob
link, so creation stopped with HTTP 500 and the temporary daemon/store were
removed. This is a safe filesystem-isolation limitation, not a model-quality or
context-precedence result.

Completing the Modelfile variant would require either a private copy/reflink of
the approximately 18 GB Qwen artifact or privileged mutation of source-blob
metadata. Neither action was taken.

## Interpretation

The earlier stable-service observation—64K remained allocated despite a smaller
request—must not be generalized. It describes that already-running service and
its request path. In a newly launched isolated daemon, server and request
settings demonstrably interact differently.

This establishes the disposable-launcher approach as viable. It does not prove
the best context, backend, server, or model for any workload.

## Cleanup and non-actions

- every successful secondary daemon was terminated; no listener remained on
  port 11435 after each completed run;
- the temporary Modelfile model store was removed after its blocked probe;
- no package, driver, Ollama version, systemd unit, firewall, Tailscale route,
  production model, or Floor source/configuration changed;
- no model was downloaded, copied, converted, or deleted.

## Next

Persist the proven disposable launcher as a small lab-only helper, then run the
llama-server baseline audit and compatibility probes. Keep the Modelfile
precedence test deferred unless a private artifact clone is explicitly wanted.
