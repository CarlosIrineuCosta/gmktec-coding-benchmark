# GMKtec Local-Inference Lab — Gate 0 Readiness

**Recorded:** 2026-08-17  
**Status:** superseded by verified direct GMKtec lab access  
**Scope:** original read-only control-host observation; corrected after
Charles supplied the approved direct diagnostic route

## Result

> **Correction — 2026-08-17:** This report records a limitation of the
> control-session sandbox resolver, not GMKtec availability. Charles confirmed
> that Tailscale and tmux access were live, supplied a one-off direct diagnostic
> address, and subsequent SSH checks verified the host name `gmktec`. The
> disposable Ollama lab, Docker installation, vLLM smoke, and later benchmark
> work then completed against that host. No static address was written to any
> configuration or documentation as a replacement for dynamic access.

At the time of the original observation, no model download, package
installation, driver change, container pull, or additional inference-stack
approval had been inferred from it.

The original observation was that the control host's sandbox could not reach
the lab host through the dynamic name `gmktec`:

- the existing user SSH profile names `gmktec`, uses user `cdc`, and references
  the existing GMKtec identity file;
- the local default SSH configuration is rejected because a system include is
  owned by `nobody` rather than a trusted owner;
- bypassing that include and using the user profile still fails because neither
  `gmktec` nor its MagicDNS FQDN resolves on this host;
- no running `tailscaled` service or usable `tailscale` command was observed on
  the control host.

No IP address was inferred or pinned by that Gate 0 check. The later
owner-provided direct diagnostic route did not alter that non-persistence rule.

## Existing evidence preserved

The local benchmark repository still contains the prior controlled basis:

- Qwen3-Coder 30B, Q4_K_M, was served with llama.cpp build
  `b10454-4df29be4f` on Vulkan/RADV;
- the controlled `llama-server` tool route passed at 8K, 16K, 32K, and 64K;
- the prior Ollama comparison observed the stable daemon at 64K despite smaller
  request `num_ctx` options. That observation is the reason for the new
  isolated precedence experiment; it is not treated as a universal rule.

The benchmark repository has pre-existing untracked work. It has not been
modified by this Gate 0 check.

## Historical next action

This is no longer an active blocker. The actual next lab actions are recorded
in the later compatibility, context-precedence, and provenance reports.

## Actions explicitly not taken

- no change to SSH, DNS, Tailscale, system services, firewall, drivers, or
  packages;
- no connection to GMKtec;
- no Ollama, llama-server, or vLLM process started, stopped, or reconfigured;
- no model artifact pulled, changed, or deleted;
- no Floor runtime, provider route, registry, or source code changed.
