# Benchmark notes

This is the preserved model-generated result of the supervised gallery task.
It is a local-only working demo, not production software.

- Candidate: `Qwen3.8-Flash-Next-UD-Q3_K_XL` from
  `unsloth/Qwen3.8-Flash-Next-GGUF`, revision
  `c8b5954a88c2775c546b92593eda40ea041d3176`.
- Artifact shards and SHA-256:
  - `Qwen3.8-Flash-Next-UD-Q3_K_XL-00001-of-00003.gguf`:
    `f2ef4328929d8b8c8930e2856eef52128dd4ce3425302f04bc3c657431cc4c49`
  - `Qwen3.8-Flash-Next-UD-Q3_K_XL-00002-of-00003.gguf`:
    `7d230e7c9421d868b89eebaf23033af0ea1a4e046956df00fb156814fb62346e`
  - `Qwen3.8-Flash-Next-UD-Q3_K_XL-00003-of-00003.gguf`:
    `21d4f90f9cd7b7c3a1582667c20cb22f7b03de895b88a23bb20aaeaa44f2c199`
- Run: 2026-09-02, 131072-token context, reasoning on / xhigh / preserve,
  no completion-token cap, unlimited transport timeout.
- Task: the unchanged `TASK.md` in this directory. It required twelve supplied
  public-domain images plus twelve locally acquired Met Open Access images,
  category filtering, responsive layout, and a keyboard-accessible lightbox.
- Supervision: after 10 completed research turns and 20 searches, Owner
  directed transition to the unchanged development work. Follow-up corrections
  fixed added-record-only validation and the missing local module entry point.
  No task or test files were changed.
- Terminal evidence: production build passed and independent browser validation
  passed. The model did not invoke the final E2E command after the successful
  build; this is recorded as an omission.

See `docs/reports/2026-09-02-qwen38-gallery-supervised-comparison.md` for the
comparison and `evidence/2026-09-02-qwen38-gallery-comparison/` for browser
captures.
