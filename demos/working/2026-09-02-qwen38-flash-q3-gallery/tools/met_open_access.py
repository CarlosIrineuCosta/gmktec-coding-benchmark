"""Small workspace-only helper for Met Open Access research and downloads.

The helper intentionally permits only the official Met collection API and the
image URL returned by that API. It is for a benchmark acquisition pass, never
for runtime use by the generated gallery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


API = "https://collectionapi.metmuseum.org/public/collection/v1"
RIGHTS_PAGE = "https://www.metmuseum.org/hubs/open-access"


def jpeg_size(data: bytes) -> tuple[int, int]:
    """Return JPEG width and height without an extra package or shell command."""
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("download is not a JPEG")
    offset = 2
    while offset + 9 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        length = int.from_bytes(data[offset:offset + 2], "big")
        if length < 2 or offset + length > len(data):
            break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            return (
                int.from_bytes(data[offset + 5:offset + 7], "big"),
                int.from_bytes(data[offset + 3:offset + 5], "big"),
            )
        offset += length
    raise ValueError("JPEG dimensions were not found")


def get_json(path: str) -> dict:
    request = urllib.request.Request(f"{API}{path}", headers={"User-Agent": "gallery-concept-benchmark/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def object_record(object_id: int) -> dict:
    item = get_json(f"/objects/{object_id}")
    if not item.get("isPublicDomain") or not item.get("primaryImage"):
        raise ValueError("object is not an Open Access public-domain image")
    return item


def command_search(query: str) -> int:
    payload = get_json("/search?" + urllib.parse.urlencode({"q": query, "hasImages": "true"}))
    results: list[dict] = []
    for object_id in (payload.get("objectIDs") or [])[:30]:
        try:
            item = object_record(int(object_id))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        results.append({
            "object_id": item["objectID"], "title": item.get("title"),
            "creator": item.get("artistDisplayName") or None,
            "date": item.get("objectDate") or None,
            "department": item.get("department") or None,
            "source_page": f"https://www.metmuseum.org/art/collection/search/{item['objectID']}",
        })
        if len(results) == 12:
            break
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


def command_download(object_id: int, filename: str) -> int:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.jpg", filename):
        raise ValueError("filename must be a lowercase .jpg filename")
    item = object_record(object_id)
    image_url = item["primaryImage"]
    host = urllib.parse.urlparse(image_url).hostname or ""
    if not host.endswith("metmuseum.org"):
        raise ValueError("Met API returned an unexpected image host")
    request = urllib.request.Request(image_url, headers={"User-Agent": "gallery-concept-benchmark/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    width, height = jpeg_size(data)
    target = Path("public/images") / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(json.dumps({
        "id": f"met-{object_id}", "local_filename": filename,
        "title": item.get("title") or f"Met object {object_id}",
        "creator": item.get("artistDisplayName") or None,
        "date": item.get("objectDate") or None,
        "institution": "The Metropolitan Museum of Art", "rights": "CC0",
        "source_page": f"https://www.metmuseum.org/art/collection/search/{object_id}",
        "rights_page": RIGHTS_PAGE, "download_url": image_url,
        "sha256": hashlib.sha256(data).hexdigest(), "width": width,
        "height": height, "category": "UNSET",
    }, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    search = commands.add_parser("search")
    search.add_argument("query")
    download = commands.add_parser("download")
    download.add_argument("object_id", type=int)
    download.add_argument("filename")
    args = parser.parse_args()
    if args.command == "search":
        return command_search(args.query)
    return command_download(args.object_id, args.filename)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"asset tool error: {error}", file=sys.stderr)
        raise SystemExit(2)
