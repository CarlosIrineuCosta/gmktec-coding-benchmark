"""Small, auditable OpenAI-compatible tool contract for isolated worktrees."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


TOOL_DEFINITIONS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read a UTF-8 file in the isolated workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files below a workspace-relative directory.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "search_files", "description": "Find a literal UTF-8 text fragment below the isolated workspace.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write a UTF-8 file in the isolated workspace.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "patch_file", "description": "Replace one exact UTF-8 fragment in an isolated workspace file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}}},
    {"type": "function", "function": {"name": "run_command", "description": "Run a bounded command inside the isolated workspace.", "parameters": {"type": "object", "properties": {"argv": {"type": "array", "items": {"type": "string"}}}, "required": ["argv"]}}},
]


class WorkspaceTools:
    def __init__(self, workspace: Path, command_timeout_seconds: int = 120) -> None:
        self.workspace = workspace.resolve()
        self.command_timeout_seconds = command_timeout_seconds

    def _path(self, relative: str) -> Path:
        target = (self.workspace / relative).resolve()
        if target != self.workspace and self.workspace not in target.parents:
            raise ValueError("path escapes isolated workspace")
        return target

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "read_file":
            return {"content": self._path(arguments["path"]).read_text(encoding="utf-8")}
        if name == "list_files":
            root = self._path(arguments.get("path", "."))
            return {"files": sorted(str(path.relative_to(self.workspace)) for path in root.rglob("*") if path.is_file())}
        if name == "search_files":
            query = arguments["query"]
            if not isinstance(query, str) or not query:
                raise ValueError("query must be a non-empty string")
            matches: list[dict[str, object]] = []
            for path in self.workspace.rglob("*"):
                if not path.is_file() or len(matches) >= 200:
                    continue
                try:
                    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                        if query in line:
                            matches.append({"path": str(path.relative_to(self.workspace)), "line": number, "text": line[:1000]})
                            if len(matches) >= 200:
                                break
                except UnicodeDecodeError:
                    continue
            return {"matches": matches}
        if name == "write_file":
            target = self._path(arguments["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(arguments["content"], encoding="utf-8")
            return {"written": str(target.relative_to(self.workspace))}
        if name == "patch_file":
            target = self._path(arguments["path"])
            old, new = arguments["old"], arguments["new"]
            if not isinstance(old, str) or not isinstance(new, str) or not old:
                raise ValueError("old and new must be strings and old must be non-empty")
            content = target.read_text(encoding="utf-8")
            if content.count(old) != 1:
                raise ValueError("old fragment must occur exactly once")
            target.write_text(content.replace(old, new), encoding="utf-8")
            return {"patched": str(target.relative_to(self.workspace))}
        if name == "run_command":
            argv = arguments["argv"]
            if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
                raise ValueError("argv must be a non-empty string array")
            completed = subprocess.run(argv, cwd=self.workspace, text=True, capture_output=True, timeout=self.command_timeout_seconds, check=False)
            return {"exit_code": completed.returncode, "stdout": completed.stdout[-30000:], "stderr": completed.stderr[-30000:]}
        raise ValueError(f"tool is not allowed: {name}")


def tool_result_for_log(name: str, arguments: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {"tool": name, "arguments": arguments, "result": result, "result_json": json.dumps(result, sort_keys=True)}
