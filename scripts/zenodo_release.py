"""Zenodo release helper for the frozen submission artifacts.

Two explicit subcommands, both read ZENODO_TOKEN from the repository ``.env``:

  reserve  --from-deposition <id>
      Create a new version draft of the concept record and print the reserved
      version DOI.  Nothing is uploaded and nothing is published.

  publish  --deposition <draft id> --metadata <json> --files <paths...>
      Replace the draft's files with the given files, set its metadata from the
      JSON file, and publish.  Prints the published DOI and the SHA-256 of every
      file as served by Zenodo after publication.

The helper never touches historical versions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
API = "https://zenodo.org/api"


def token() -> str:
    env = (ROOT / ".env").read_text(encoding="utf-8")
    for line in env.splitlines():
        if line.startswith("ZENODO_TOKEN="):
            return line.split("=", 1)[1].strip()
    value = os.environ.get("ZENODO_TOKEN")
    if not value:
        raise SystemExit("ZENODO_TOKEN not found")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def request(method: str, url: str, **kwargs):
    kwargs.setdefault("params", {})
    kwargs["params"]["access_token"] = token()
    for attempt in range(4):
        response = requests.request(method, url, timeout=600, **kwargs)
        if response.status_code in (502, 503, 504) and attempt < 3:
            time.sleep(5 * (attempt + 1))
            continue
        break
    if response.status_code >= 400:
        raise SystemExit(f"{method} {url} -> {response.status_code}: {response.text[:800]}")
    return response


def reserve(args: argparse.Namespace) -> int:
    response = request("POST", f"{API}/deposit/depositions/{args.from_deposition}/actions/newversion")
    draft_url = response.json()["links"]["latest_draft"]
    draft = request("GET", draft_url).json()
    prereserve = draft.get("metadata", {}).get("prereserve_doi", {})
    print(json.dumps({
        "draft_id": draft["id"],
        "draft_url": draft_url,
        "reserved_doi": prereserve.get("doi"),
        "conceptdoi": draft.get("conceptdoi"),
        "state": draft.get("state"),
    }, indent=2))
    return 0


def publish(args: argparse.Namespace) -> int:
    deposition = request("GET", f"{API}/deposit/depositions/{args.deposition}").json()
    if deposition.get("submitted"):
        raise SystemExit("deposition is already published")
    # remove files inherited from the previous version
    for entry in request("GET", f"{API}/deposit/depositions/{args.deposition}/files").json():
        request("DELETE", f"{API}/deposit/depositions/{args.deposition}/files/{entry['id']}")
    bucket = deposition["links"]["bucket"]
    local_hashes = {}
    for path_str in args.files:
        path = Path(path_str)
        local_hashes[path.name] = sha256(path)
        with path.open("rb") as stream:
            request("PUT", f"{bucket}/{path.name}", data=stream)
        print(f"uploaded {path.name}")
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    request(
        "PUT",
        f"{API}/deposit/depositions/{args.deposition}",
        json={"metadata": metadata},
        headers={"Content-Type": "application/json"},
    )
    published = request("POST", f"{API}/deposit/depositions/{args.deposition}/actions/publish").json()
    record = request("GET", published["links"]["record"]).json()
    served = {}
    for entry in record.get("files", []):
        checksum = entry.get("checksum", "")
        served[entry["key"]] = checksum
    print(json.dumps({
        "doi": published.get("doi"),
        "record_url": published["links"].get("record_html"),
        "local_sha256": local_hashes,
        "zenodo_checksums": served,
    }, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("reserve")
    r.add_argument("--from-deposition", required=True)
    r.set_defaults(func=reserve)
    p = sub.add_parser("publish")
    p.add_argument("--deposition", required=True)
    p.add_argument("--metadata", required=True)
    p.add_argument("--files", nargs="+", required=True)
    p.set_defaults(func=publish)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
