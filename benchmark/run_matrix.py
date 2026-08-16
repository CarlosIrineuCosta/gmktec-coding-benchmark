from __future__ import annotations

import argparse
import json
import os
import shutil
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import MAIN_CONTEXT, PROFILES, RESULTS, ROOT, SYSTEMS, TASK_IDS, TIMEOUT_SECONDS
from .ollama_agent import run as run_ollama, unload, wait_empty
from .prepare import packet_hash, packet_text, prepare_worktree
from .sandbox import bwrap


_SAFE_ENV_KEYS = (
    "PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM",
    "SSL_CERT_FILE", "SSL_CERT_DIR",
)


def _clean_env() -> dict[str, str]:
    """Return a minimal environment so candidates cannot inspect host secrets."""
    return {key: os.environ[key] for key in _SAFE_ENV_KEYS if key in os.environ}


def _read_export(path: Path, wanted: str) -> str:
    """Read exactly one shell-style exported value without evaluating the file."""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        if not line.startswith(f"{wanted}="):
            continue
        value = line.split("=", 1)[1].strip()
        parsed = shlex.split(value, comments=True, posix=True)
        if len(parsed) != 1 or not parsed[0]:
            raise RuntimeError(f"invalid {wanted} entry in {path}")
        return parsed[0]
    raise RuntimeError(f"{wanted} is not configured in {path}")


def _run_id(system_id: str, task_id: str, context: int) -> str:
    return f"{system_id}__{task_id}__ctx{context}"


def _prompt(task_id: str, context: int) -> str:
    return (
        packet_text(task_id)
        + f"\n\nBenchmark contract: requested context {context} tokens. Work only in the current repository. "
          "Do not use native web/search/fetch tools, credentials, or external repositories. Run tests before finishing."
    )


def _native_command(system: dict, worktree: Path, prompt: str, context: int):
    harness = system["harness"]
    if harness == "codex":
        profile = PROFILES / "codex"
        command = [
            "codex", "exec", "--ephemeral", "--json", "--ignore-user-config",
            "-m", system["model"], "-c", 'model_reasoning_effort="high"',
            "-c", f"model_context_window={context}", "-s", "workspace-write",
            "-c", 'approval_policy="never"', "-C", "/tmp/workspace", prompt,
        ]
        env = _clean_env(); env["CODEX_HOME"] = "/tmp/profile"
        return bwrap(worktree, profile, command), env
    if harness == "claude":
        profile = PROFILES / "zai-claude"
        template = profile / "settings.template.json"
        settings = profile / "settings.json"
        if not settings.exists(): shutil.copy2(template, settings)
        command = [
            "claude", "--print", "--model", system["model"], "--effort", "high",
            "--permission-mode", "acceptEdits",
            "--allowedTools", "Read,Edit,Write,Glob,Grep,Bash(python3:*),Bash(pytest:*),Bash(git diff:*),Bash(git status:*),Bash(rg:*),Bash(sed:*),Bash(find:*),Bash(ls:*)",
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--disallowedTools", "WebSearch,WebFetch", "--output-format", "stream-json",
            "--verbose", "--no-session-persistence", prompt,
        ]
        env = _clean_env(); env["CLAUDE_CONFIG_DIR"] = "/tmp/profile"
        env["ANTHROPIC_BASE_URL"] = "https://api.z.ai/api/anthropic"
        env["ANTHROPIC_API_KEY"] = _read_export(
            Path("/home/cdc/.config/secrets/ai.env"), "GLM_API_KEY"
        )
        for key in ("ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL"):
            env[key] = system["model"]
        env["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = str(context)
        return bwrap(worktree, profile, command), env
    if harness == "kimi":
        profile = PROFILES / "kimi"
        # Prompt mode is non-interactive and inherits the profile's auto permission
        # mode. Kimi 0.31.1 rejects an explicit --auto combined with --prompt.
        command = ["/home/cdc/.kimi-code/bin/kimi", "-m", system["model"], "-p", prompt, "--output-format", "stream-json"]
        env = _clean_env(); env["KIMI_CODE_HOME"] = "/tmp/profile"
        return bwrap(worktree, profile, command), env
    raise ValueError(harness)


def run_one(system: dict, task_id: str, context: int, dry_run=False):
    run_id = _run_id(system["id"], task_id, context)
    result_path = RESULTS / f"{run_id}.json"
    if result_path.exists(): return {"run_id": run_id, "status": "already_recorded"}
    if dry_run: return {"run_id": run_id, "harness": system["harness"], "model": system["model"]}
    worktree = prepare_worktree(run_id, task_id)
    started = time.monotonic(); started_at = datetime.now(timezone.utc).isoformat()
    record = {
        "run_id": run_id, "system_id": system["id"], "harness": system["harness"],
        "model": system["model"], "task": task_id, "context_requested": context,
        "task_packet_sha256": packet_hash(task_id), "started_at": started_at,
        "timeout_seconds": TIMEOUT_SECONDS, "native_web_enabled": False,
    }
    try:
        if system["harness"] == "ollama":
            unloaded_before = unload(system["model"])
            empty_before = unloaded_before or wait_empty(max(0, TIMEOUT_SECONDS - (time.monotonic() - started)))
            record["empty_before"] = empty_before
            if not empty_before:
                raise TimeoutError("GMKtec did not become empty before the run deadline")
            remaining = max(0, TIMEOUT_SECONDS - (time.monotonic() - started))
            final, transcript, metrics, stop_reason = run_ollama(
                system["model"], _prompt(task_id, context), worktree, context,
                max_seconds=remaining,
            )
            record.update(metrics); record["final_message"] = final; record["transcript"] = transcript
            record["stop_reason"] = stop_reason; record["unloaded_before"] = unloaded_before
            record["unloaded_after"] = unload(system["model"])
            record["status"] = "timeout" if stop_reason == "hard_timeout" else "completed"
        else:
            command, env = _native_command(system, worktree, _prompt(task_id, context), context)
            completed = subprocess.run(command, cwd=worktree, env=env, text=True, capture_output=True, timeout=TIMEOUT_SECONDS)
            record["exit_code"] = completed.returncode; record["stdout"] = completed.stdout[-2_000_000:]
            record["stderr"] = completed.stderr[-500_000:]
            record["status"] = "completed" if completed.returncode == 0 else "failed"
            record["stop_reason"] = "process_exit"
    except subprocess.TimeoutExpired as exc:
        record["status"] = "timeout"; record["stop_reason"] = "hard_timeout"
        record["stdout"] = (exc.stdout or "")[-2_000_000:] if isinstance(exc.stdout, str) else ""
        record["stderr"] = (exc.stderr or "")[-500_000:] if isinstance(exc.stderr, str) else ""
    except Exception as exc:
        record["status"] = "failed_preflight_or_runtime"; record["stop_reason"] = type(exc).__name__
        record["error"] = str(exc)
    finally:
        if system["harness"] == "ollama" and "unloaded_after" not in record:
            record["unloaded_after"] = unload(system["model"])
    record["wall_seconds"] = time.monotonic() - started
    diff = subprocess.run(["git", "diff", "--stat"], cwd=worktree, text=True, capture_output=True)
    record["diff_stat"] = diff.stdout
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    RESULTS.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"run_id": run_id, "status": record["status"], "wall_seconds": record["wall_seconds"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", type=int, default=MAIN_CONTEXT)
    parser.add_argument("--system", action="append", help="system id; repeatable")
    parser.add_argument("--task", action="append", choices=TASK_IDS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    systems = [row for row in SYSTEMS if not args.system or row["id"] in args.system]
    tasks = args.task or TASK_IDS
    for system in systems:
        for task in tasks:
            print(json.dumps(run_one(system, task, args.context, args.dry_run)), flush=True)


if __name__ == "__main__": main()
