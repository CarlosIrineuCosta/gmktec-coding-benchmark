# 2026-08-30 real-work evaluation suite

This suite is prepared for an owner-selected two-model pilot. No model is
selected in this tracked material. Each actual candidate run receives a fresh,
disposable worktree, a fresh server lifecycle, and its own private evidence
directory.

- `gallery/`: greenfield web-generation contract and observable acceptance.
- `code-review/`: public reviewer-output contract; held-out defects and gold
  data remain in `data/private/`.
- `translation/`: EN -> PT-BR contract awaiting owner-supplied source text.
- `pilot.json`: deliberately incomplete selection configuration.

The model does not receive hidden implementation requirements, private source,
or another candidate's evidence.
