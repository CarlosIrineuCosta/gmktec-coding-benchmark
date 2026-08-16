# Task: Daily Ops Trello and one-shot voice vertical

Extend the supplied clean Daily Ops snapshot. Retain read-only Gmail ingestion.

- Add a real gated Trello adapter targeting exactly one runtime-configured
  dedicated Daily Ops Inbox. Every external write requires explicit proposal
  approval. Fence retries/response loss against duplicate cards. Never
  hard-code a board/list, inspect credentials, or perform a live canary.
- Add `STTAdapter.transcribe(audio, language_hint) -> Transcript` and a
  Tailscale-only mobile/PWA one-shot recording workflow. Visible states:
  recorded, uploading, transcribing, proposal saved, failed/retryable.
- Persist failed recordings for retry. Delete audio only after transcript and
  editable proposal are durably persisted. Support PT-BR, English, mixed, and
  auto hints. No voice commands or conversational agent.
- Keep fixture mode safe. Add tests for Trello gating/deduplication, approval,
  mobile retry, bilingual/mixed capture, state transitions, and failures.

Run the existing 48-test baseline plus new tests. No Gmail/Trello writes,
public deploy, Whisper install, or canonical-repo mutation during this task.
