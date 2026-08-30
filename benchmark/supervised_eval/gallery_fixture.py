"""Materialize the fixed public-domain gallery corpus into ignored local data."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        length = int.from_bytes(data[index:index + 2], "big")
        if 0xC0 <= marker <= 0xC3 and index + 7 < len(data):
            return int.from_bytes(data[index + 5:index + 7], "big"), int.from_bytes(data[index + 3:index + 5], "big")
        index += length
    return None


def dimensions(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    return _jpeg_dimensions(data)


def materialize(sources: list[dict[str, Any]], output_dir: Path, fetch: bool) -> list[dict[str, Any]]:
    if len(sources) != 12:
        raise ValueError("gallery corpus must have exactly 12 images")
    if len({item["id"] for item in sources}) != len(sources):
        raise ValueError("gallery source ids must be unique")
    records: list[dict[str, Any]] = []
    for item in sources:
        required = {"id", "local_filename", "creator", "license", "source_page", "download_url"}
        if set(item) != required or item["license"] != "public-domain":
            raise ValueError("gallery sources must have fixed public-domain provenance")
        record = {key: item[key] for key in required if key != "download_url"}
        target = output_dir / item["local_filename"]
        if fetch and not target.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            request = urllib.request.Request(item["download_url"], headers={"User-Agent": "gmktec-coding-benchmark/2026-08-30"})
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read()
            except OSError as exc:
                raise RuntimeError(f"gallery download failed for {item['id']}: {exc}") from exc
            target.write_bytes(data)
        if target.exists():
            data = target.read_bytes()
            size = dimensions(data)
            if size is None:
                raise ValueError(f"unsupported image data for {target.name}")
            record.update({"sha256": hashlib.sha256(data).hexdigest(), "width": size[0], "height": size[1]})
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true", help="download source images; otherwise validate the planned corpus")
    args = parser.parse_args()
    records = materialize(json.loads(args.sources.read_text(encoding="utf-8")), args.output_dir, args.fetch)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
