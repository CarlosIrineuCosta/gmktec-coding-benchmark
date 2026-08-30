"""One-turn OpenAI-compatible tool exchange with full private trajectory logging."""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Any, Callable

from .evidence import EvidenceStore
from .harness import WorkspaceTools, tool_result_for_log


Post = Callable[[dict[str, Any]], dict[str, Any]]


class OpenAICompatibleSession:
    """A minimal primary harness; callers own the active supervision loop."""

    def __init__(self, base_url: str, model: str, evidence: EvidenceStore, tools: WorkspaceTools, post: Post | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.evidence = evidence
        self.tools = tools
        self._post = post or self._http_post

    def _http_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=900) as response:
            return json.loads(response.read().decode())

    def one_turn(
        self,
        messages: list[dict[str, Any]],
        tool_definitions: list[dict[str, Any]],
        request_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {"model": self.model, "messages": messages, "tools": tool_definitions, "tool_choice": "auto"}
        if request_options:
            forbidden = {"model", "messages", "tools", "tool_choice"}.intersection(request_options)
            if forbidden:
                raise ValueError(f"request options cannot override protocol keys: {sorted(forbidden)}")
            payload.update(request_options)
        started = time.monotonic()
        response = self._post(payload)
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        choices = response.get("choices") or []
        if not choices or not isinstance(choices[0].get("message"), dict):
            raise ValueError("OpenAI-compatible response has no assistant message")
        assistant = choices[0]["message"]
        self.evidence.event("model_turn", request=payload, response=response, elapsed_ms=elapsed_ms)
        tool_results: list[dict[str, Any]] = []
        for call in assistant.get("tool_calls") or []:
            function = call.get("function") or {}
            name = function.get("name")
            try:
                arguments = json.loads(function.get("arguments", "{}"))
                result = self.tools.call(name, arguments)
            except Exception as exc:
                arguments = {"unparsed": function.get("arguments")}
                result = {"rejected": f"{type(exc).__name__}: {exc}"}
            record = tool_result_for_log(name or "<missing>", arguments, result)
            record["tool_call_id"] = call.get("id")
            tool_results.append(record)
            self.evidence.event("tool_call", **record)
        return {"assistant": assistant, "tool_results": tool_results, "usage": response.get("usage"), "elapsed_ms": elapsed_ms}
