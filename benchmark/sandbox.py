from __future__ import annotations

import shutil
from pathlib import Path

from .config import ROOT


def bwrap(worktree: Path, profile: Path | None, command: list[str]) -> list[str]:
    command = list(command)
    args = [
        "bwrap", "--die-with-parent", "--new-session",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/bin", "/bin",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
        "--dir", "/etc", "--ro-bind", "/etc/ssl", "/etc/ssl",
        "--ro-bind", str(Path("/etc/resolv.conf").resolve()), "/etc/resolv.conf",
        "--ro-bind", "/etc/hosts", "/etc/hosts",
        "--ro-bind", "/etc/nsswitch.conf", "/etc/nsswitch.conf",
        "--ro-bind", "/etc/passwd", "/etc/passwd",
        "--ro-bind", "/etc/group", "/etc/group",
        "--dir", "/home", "--dir", "/home/cdc",
        "--dir", "/opt", "--dir", "/opt/benchmark-bin",
        "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
        "--dir", "/tmp/workspace", "--bind", str(worktree), "/tmp/workspace",
        "--setenv", "HOME", "/tmp/profile",
        "--setenv", "PATH", "/opt/codex-runtime/bin:/opt/benchmark-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    ]
    if command[0] == "claude":
        source = Path("/home/cdc/.local/share/claude/versions/2.1.226")
        args += ["--ro-bind", str(source), "/opt/benchmark-bin/claude"]
        command[0] = "/opt/benchmark-bin/claude"
    elif command[0] == "/home/cdc/.kimi-code/bin/kimi":
        args += ["--ro-bind", command[0], "/opt/benchmark-bin/kimi"]
        command[0] = "/opt/benchmark-bin/kimi"
    elif command[0] == "codex":
        runtime = Path("/home/cdc/.nvm/versions/node/v22.14.0")
        args += ["--ro-bind", str(runtime), "/opt/codex-runtime"]
        command[0] = "/opt/codex-runtime/bin/codex"
    if profile:
        profile.mkdir(parents=True, exist_ok=True)
        args += ["--dir", "/tmp/profile", "--bind", str(profile), "/tmp/profile"]
    return args + ["--chdir", "/tmp/workspace", *command]
