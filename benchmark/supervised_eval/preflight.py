"""Phase-0 checks for the full local coding campaign.

The checker is intentionally read-only except for its single JSON evidence
file.  It verifies the exact input paths supplied by the campaign operator;
it does not search the host, select models, or modify services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .campaign import CAMPAIGN_ID
from .private_fixture import validate_private_code_review_fixture


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def command(argv: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> dict[str, Any]:
    effective_env = {**os.environ, **(env or {})}
    executable = shutil.which(argv[0], path=effective_env.get("PATH"))
    if executable is None:
        return {"ok": False, "reason": "unavailable", "argv": argv}
    try:
        result = subprocess.run(argv, cwd=cwd, env=effective_env, text=True, capture_output=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}", "argv": argv}
    return {
        "ok": result.returncode == 0,
        "argv": argv,
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-2000:],
    }


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def gallery_check(manifest_path: Path, image_root: Path) -> dict[str, Any]:
    try:
        records = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(records, list) or len(records) != 12:
            raise ValueError("manifest must contain exactly 12 image records")
        mismatches = []
        for record in records:
            filename, expected = record.get("local_filename"), record.get("sha256")
            image = image_root / str(filename)
            if not image.is_file() or not isinstance(expected, str) or hash_file(image) != expected:
                mismatches.append(str(filename))
        return {"ok": not mismatches, "records": len(records), "mismatches": mismatches}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}


def browser_smoke(node: Path, gallery_workspace: Path) -> dict[str, Any]:
    script = (
        "const { chromium } = require('playwright');"
        "(async()=>{const b=await chromium.launch({headless:true});"
        "for(const vp of [{width:1440,height:900},{width:390,height:844}]){"
        "const p=await b.newPage({viewport:vp});await p.setContent('<main>phase0</main>');"
        "if(await p.locator('main').textContent()!=='phase0')throw new Error('content mismatch');await p.close();}"
        "await b.close();console.log('chromium-both-viewports-ok');})().catch(e=>{console.error(e);process.exit(1)});"
    )
    return command([str(node), "-e", script], cwd=gallery_workspace, env={"PATH": f"{node.parent}:{os.environ.get('PATH', '')}"})


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Record full-campaign Phase-0 evidence")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", action="append", default=[], type=Path)
    parser.add_argument("--server", required=True, type=Path)
    parser.add_argument("--node", required=True, type=Path)
    parser.add_argument("--gallery-workspace", required=True, type=Path)
    parser.add_argument("--gallery-manifest", required=True, type=Path)
    parser.add_argument("--gallery-images", required=True, type=Path)
    parser.add_argument("--review-root", required=True, type=Path)
    parser.add_argument("--port", action="append", type=int, default=[])
    args = parser.parse_args()
    checks: dict[str, Any] = {}
    for utility in ("git", "curl", "jq", "python3"):
        checks[f"utility:{utility}"] = command([utility, "--version"])
    node_path = f"{args.node.parent}:{os.environ.get('PATH', '')}"
    checks["node"] = command([str(args.node), "--version"], env={"PATH": node_path})
    checks["npm"] = command([str(args.node.parent / "npm"), "--version"], env={"PATH": node_path})
    checks["npx_playwright"] = command([str(args.node.parent / "npx"), "playwright", "--version"], cwd=args.gallery_workspace, env={"PATH": node_path})
    checks["chromium_both_viewports"] = browser_smoke(args.node, args.gallery_workspace)
    checks["gallery_corpus"] = gallery_check(args.gallery_manifest, args.gallery_images)
    try:
        checks["private_review_fixture"] = {"ok": True, **validate_private_code_review_fixture(args.review_root)}
    except (OSError, ValueError, FileNotFoundError) as exc:
        checks["private_review_fixture"] = {"ok": False, "reason": f"{type(exc).__name__}: {exc}"}
    checks["llama_server"] = {"ok": args.server.is_file() and args.server.stat().st_mode & 0o111 != 0, "path": str(args.server)}
    checks["models"] = {"ok": len(args.model) == 9 and all(path.is_file() for path in args.model), "count": len(args.model), "bytes": [path.stat().st_size if path.is_file() else None for path in args.model]}
    checks["ports"] = {"ok": all(port_free(port) for port in args.port), "ports": args.port}
    checks["free_disk"] = {"ok": shutil.disk_usage(args.output.parent).free > 100 * 1024**3, "free_bytes": shutil.disk_usage(args.output.parent).free}
    checks["drm_telemetry_source"] = {"ok": Path("/sys/class/drm").is_dir()}
    status = "passed" if all(bool(check.get("ok")) for check in checks.values()) else "failed"
    payload = {"campaign_id": CAMPAIGN_ID, "started_at": now(), "finished_at": now(), "status": status, "checks": checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite preflight: {args.output}")
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "failed_checks": [name for name, check in checks.items() if not check.get("ok")]}, sort_keys=True))
    return 0 if status == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
