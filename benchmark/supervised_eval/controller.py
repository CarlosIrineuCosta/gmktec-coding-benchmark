"""Turn-granular, restartable controller for a supervised candidate run.

The controller deliberately stops after every assistant/tool exchange.  A
caller (Codex in the real pilot) must inspect the durable state and explicitly
ask for the next turn, an allowed intervention, or a terminal classification.
It therefore cannot become an autonomous hidden supervisor.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import InterventionClass, RunPhase, TerminalClass
from .evidence import EvidenceStore, _write_json, utc_now
from .harness import TOOL_DEFINITIONS, WorkspaceTools
from .session import OpenAICompatibleSession


STATE_FILE = "controller-state.json"


def _state_path(store: EvidenceStore) -> Path:
    return store.run_dir / STATE_FILE


@dataclass
class TurnResult:
    assistant: dict[str, Any]
    tool_results: list[dict[str, Any]]
    elapsed_ms: float
    usage: dict[str, Any] | None

    def compact(self) -> dict[str, Any]:
        content = self.assistant.get("content")
        return {
            "assistant_has_content": bool(content and str(content).strip()),
            "tool_call_count": len(self.tool_results),
            "tool_names": [item["tool"] for item in self.tool_results],
            "elapsed_ms": self.elapsed_ms,
            "usage": self.usage,
        }


class PilotRunController:
    """Persist a primary native-tool conversation one model turn at a time."""

    def __init__(self, evidence_root: Path, run_id: str) -> None:
        self.store = EvidenceStore.resume(evidence_root, run_id)
        self.state_path = _state_path(self.store)
        if not self.state_path.is_file():
            raise FileNotFoundError(f"controller state does not exist: {self.state_path}")
        self.state: dict[str, Any] = json.loads(self.state_path.read_text(encoding="utf-8"))

    @classmethod
    def create(
        cls,
        evidence_root: Path,
        run_id: str,
        *,
        manifest: dict[str, Any],
        endpoint: str,
        model: str,
        workspace: Path,
        initial_message: str,
        request_options: dict[str, Any] | None = None,
        tool_environment: dict[str, str] | None = None,
    ) -> "PilotRunController":
        store = EvidenceStore(evidence_root, run_id)
        manifest = {**manifest, "run_id": run_id}
        store.write_once("manifest.json", manifest)
        store.write_once("request.json", {
            "endpoint": endpoint,
            "model": model,
            "request_options": request_options or {},
            "tool_environment": tool_environment or {},
            "tool_contract": "native_openai_function_tools",
        })
        store.transition(RunPhase.SERVER_STARTING, "disposable server command recorded by caller")
        store.transition(RunPhase.READY, "caller verified endpoint health")
        store.transition(RunPhase.AUTONOMOUS, "canonical task packet delivered without substantive assistance")
        state = {
            "version": 1,
            "created_at": utc_now(),
            "endpoint": endpoint.rstrip("/"),
            "model": model,
            "workspace": str(workspace.resolve()),
            "request_options": request_options or {},
            "tool_environment": tool_environment or {},
            "messages": [{"role": "user", "content": initial_message}],
            "turn_count": 0,
            "tool_call_count": 0,
            "supervision_checkpoints": 0,
            "terminal": False,
        }
        _write_json(_state_path(store), state)
        return cls(evidence_root, run_id)

    def _save(self) -> None:
        _write_json(self.state_path, self.state)

    def checkpoint(self, *, decision: str, basis: str, progress_observed: bool) -> None:
        if self.state["terminal"]:
            raise RuntimeError("terminal runs cannot receive supervision checkpoints")
        self.state["supervision_checkpoints"] += 1
        self.store.event(
            "supervision_checkpoint",
            checkpoint=self.state["supervision_checkpoints"],
            decision=decision,
            basis=basis,
            progress_observed=progress_observed,
            turn_count=self.state["turn_count"],
            tool_call_count=self.state["tool_call_count"],
        )
        self._save()

    def one_turn(self) -> TurnResult:
        if self.state["terminal"]:
            raise RuntimeError("terminal runs cannot receive another model turn")
        if self.store.phase not in {RunPhase.AUTONOMOUS, RunPhase.SUPERVISED_RECOVERY}:
            raise RuntimeError(f"model turn cannot start in phase {self.store.phase}")
        tools = WorkspaceTools(Path(self.state["workspace"]), environment=self.state.get("tool_environment", {}))
        session = OpenAICompatibleSession(
            self.state["endpoint"], self.state["model"], self.store, tools
        )
        result = session.one_turn(
            self.state["messages"], TOOL_DEFINITIONS, self.state["request_options"]
        )
        assistant = result["assistant"]
        self.state["messages"].append(assistant)
        for item in result["tool_results"]:
            self.state["messages"].append({
                "role": "tool",
                "tool_call_id": item.get("tool_call_id"),
                "content": item["result_json"],
            })
        self.state["turn_count"] += 1
        self.state["tool_call_count"] += len(result["tool_results"])
        compact = TurnResult(
            assistant=assistant,
            tool_results=result["tool_results"],
            elapsed_ms=result["elapsed_ms"],
            usage=result.get("usage"),
        )
        self.store.event("turn_completed", **compact.compact())
        self._save()
        return compact

    def intervene(self, intervention_class: InterventionClass, text: str, basis: str) -> None:
        if intervention_class == InterventionClass.I4_IMPLEMENTATION_FORBIDDEN:
            raise ValueError("I4 implementation assistance is forbidden")
        if self.state["terminal"]:
            raise RuntimeError("terminal runs cannot receive interventions")
        if self.store.phase == RunPhase.AUTONOMOUS:
            self.store.transition(RunPhase.SUPERVISED_RECOVERY, "allowed supervisor recovery began")
        if self.store.phase != RunPhase.SUPERVISED_RECOVERY:
            raise RuntimeError(f"intervention cannot start in phase {self.store.phase}")
        self.store.intervention(intervention_class, text, basis)
        self.state["messages"].append({"role": "user", "content": text})
        self._save()

    def terminal(self, classification: TerminalClass, reason: str, summary: str) -> None:
        if self.state["terminal"]:
            raise RuntimeError("run already terminal")
        self.store.terminal(classification, reason)
        self.store.summary(summary)
        self.state["terminal"] = True
        self.state["terminal_at"] = utc_now()
        self._save()
