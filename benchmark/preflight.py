from __future__ import annotations

import json
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .config import RESULTS, SYSTEMS
from .ollama_agent import ollama_json


def configured_export(path: Path, key: str) -> bool:
    try:
        return any(
            line.strip().removeprefix("export ").startswith(f"{key}=")
            and bool(line.strip().removeprefix("export ").split("=", 1)[1].strip())
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    except OSError:
        return False


def command_version(command, args=("--version",)):
    path = shutil.which(command)
    if not path: return {"available": False}
    result = subprocess.run([path, *args], text=True, capture_output=True, timeout=10)
    return {"available": result.returncode == 0, "path": path, "version": (result.stdout or result.stderr).strip().splitlines()[-1]}


def main():
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "hostname_contract": "gmktec",
        "provider_route": "ollama-gmktec",
        "commands": {
            "codex": command_version("codex"),
            "claude": command_version("claude"),
            "kimi": command_version("kimi"),
            "coding-helper": command_version("coding-helper"),
            "bwrap": command_version("bwrap", ("--version",)),
        },
        "auth_presence": {
            "zai": configured_export(Path("/home/cdc/.config/secrets/ai.env"), "GLM_API_KEY"),
            "kimi_profile_oauth": (Path(__file__).resolve().parent.parent / "profiles/kimi/oauth/kimi-code").exists(),
        },
        "gmktec": {"dns": False, "ollama": False, "models": []},
    }
    try:
        report["gmktec"]["addresses"] = sorted({item[4][0] for item in socket.getaddrinfo("gmktec", 11434, type=socket.SOCK_STREAM)})
        report["gmktec"]["dns"] = True
        tags = ollama_json("GET", "/api/tags")
        report["gmktec"]["ollama"] = True
        report["gmktec"]["models"] = [
            {key: row.get(key) for key in ("name", "model", "digest", "size", "details")}
            for row in tags.get("models", [])
        ]
    except Exception as exc:
        report["gmktec"]["error"] = f"{type(exc).__name__}: {exc}"
    wanted = {row["model"] for row in SYSTEMS if row["harness"] == "ollama"}
    found = {row.get("name") or row.get("model") for row in report["gmktec"]["models"]}
    normalized_found = found | {name.removesuffix(":latest") for name in found if name}
    report["gmktec"]["missing_models"] = sorted(wanted - normalized_found)
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / "preflight.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
