# Task: independent Research toolkit

Build a clean Python package and wheel with library, CLI, and MCP interfaces.
It must have no TesseraFold or The Floor dependency.

- `web_search(SearchRequest) -> SearchResponse`: Perplexity Search primary,
  Brave fallback only for typed availability, rate-limit, or server failures.
  Empty results do not trigger fallback. Record normalized ranked evidence,
  provider, query, rank, URL, title, snippet/content, dates, request ID, usage,
  cost, and fallback history.
- `web_fetch(FetchRequest) -> FetchedResource`: HTTP/S only; deny private,
  reserved, loopback, link-local, and metadata addresses; revalidate every
  redirect; enforce MIME, size, timeout, and redirect limits; record final URL,
  chain, SHA-256, timestamp, extracted text, byte count, and truncation.
- `research(ResearchRequest) -> ResearchReport`: explicit Sonar Pro synthesis
  with citations and usage. Search never escalates to research automatically.
- Export provider-neutral source IDs and Tessera review contracts. No
  `src-perplexity-*` identifiers. Credentials remain runtime environment only.

Use the standard library where practical. Add tests and prove a built wheel
installs into a blank environment. Native/harness web tools are unavailable.
