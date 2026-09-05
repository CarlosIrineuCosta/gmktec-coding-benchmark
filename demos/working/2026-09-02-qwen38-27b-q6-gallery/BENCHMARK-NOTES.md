# Benchmark notes

This is the preserved model-generated result of the supervised gallery task.
It is a local-only working demo, not production software.

- Candidate: `Qwen3.8-27B-UD-Q6_K_XL` from `unsloth/Qwen3.8-27B-GGUF`,
  revision `27af057ecb382ddfea5d12837360a8980560e3ed`.
- Artifact SHA-256:
  `701d8fa9ed214ab21bfc130cd2a7df19ca89bbef7713e2dfb19f3c63696aa917`.
- Run: 2026-09-02, 131072-token context, reasoning on / xhigh / preserve,
  no completion-token cap, unlimited transport timeout.
- Task: the unchanged `TASK.md` in this directory. It required twelve supplied
  public-domain images plus twelve locally acquired Met Open Access images,
  category filtering, responsive layout, and a keyboard-accessible lightbox.
- Supervision: after 12 completed research turns and 40 searches, Owner
  directed transition to the unchanged development work. Browser-led follow-up
  corrections fixed initial lightbox visibility/favicon handling and rendered
  category buttons. No task or test files were changed.
- Terminal evidence: production build passed; independent browser validation
  passed. The fixture E2E command reported that it had no tests to discover,
  so this is recorded as a fixture limitation, not an app assertion result.

See `docs/reports/2026-09-02-qwen38-gallery-supervised-comparison.md` for the
comparison and `evidence/2026-09-02-qwen38-gallery-comparison/` for browser
captures.
