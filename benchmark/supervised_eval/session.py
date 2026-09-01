"""One-turn OpenAI-compatible tool exchange with full private trajectory logging."""
from __future__ import annotations

import ast
import json
import re
import time
import urllib.request
from typing import Any, Callable

from .evidence import EvidenceStore
from .harness import WorkspaceTools, tool_result_for_log


Post = Callable[[dict[str, Any]], dict[str, Any]]


def parse_structured_tool_call(content: str) -> dict[str, Any] | None:
    """Parse exactly one explicitly tagged JSON or Pythonic tool action.

    Some qualified local models do not emit OpenAI ``tool_calls``.  Their
    model-card adapters instead place one action inside ``<TOOLCALL>``.  This
    parser is deliberately narrow: it never evaluates model text and accepts
    only a single named call with literal keyword arguments.
    """
    match = re.search(r"<tool_?call>\s*(.*?)\s*</tool_?call>", content, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    candidate = match.group(1).strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            expression = ast.parse(candidate, mode="eval").body
        except SyntaxError:
            return None
        if isinstance(expression, ast.List) and len(expression.elts) == 1:
            expression = expression.elts[0]
        if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name) or expression.args:
            return None
        arguments: dict[str, Any] = {}
        for keyword in expression.keywords:
            if keyword.arg is None:
                return None
            try:
                arguments[keyword.arg] = ast.literal_eval(keyword.value)
            except (ValueError, TypeError, SyntaxError):
                return None
        return {"name": expression.func.id, "arguments": arguments}
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, dict) or not isinstance(value.get("name"), str) or not isinstance(value.get("arguments"), dict):
        return None
    return {"name": value["name"], "arguments": value["arguments"]}


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
        tool_contract: str = "native_openai_function_tools",
    ) -> dict[str, Any]:
        if tool_contract not in {"native_openai_function_tools", "structured_adapter"}:
            raise ValueError(f"unsupported tool contract: {tool_contract}")
        payload = {"model": self.model, "messages": messages}
        if tool_contract == "native_openai_function_tools":
            payload.update({"tools": tool_definitions, "tool_choice": "auto"})
        if request_options:
            forbidden = {"model", "messages"}.intersection(request_options)
            if tool_contract == "native_openai_function_tools":
                forbidden |= {"tools", "tool_choice"}.intersection(request_options)
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
        calls = assistant.get("tool_calls") or []
        if tool_contract == "structured_adapter":
            action = parse_structured_tool_call(str(assistant.get("content") or ""))
            calls = ([{"id": None, "function": {"name": action["name"], "arguments": json.dumps(action["arguments"])}}]
                     if action else [])
        for call in calls:
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
