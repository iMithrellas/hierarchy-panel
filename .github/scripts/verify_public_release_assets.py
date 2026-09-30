#!/usr/bin/env python3
"""Verify release assets are publicly served and byte-for-byte match local files."""

import hashlib
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "jira-panel-release-verifier"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read()
    except HTTPError as error:
        with error:
            raise


def verify(repository: str, tag: str, archive_path: str, checksum_path: str) -> int:
    endpoint = (
        f"https://api.github.com/repos/{repository}/releases/tags/"
        f"{quote(tag, safe='')}"
    )
    release = json.loads(fetch(endpoint))
    if release.get("draft") or not release.get("prerelease"):
        raise ValueError("release must remain a published prerelease until verification completes")

    local_archive = Path(archive_path).read_bytes()
    local_checksum = Path(checksum_path).read_bytes()
    expected_sha1 = hashlib.sha1(local_archive).hexdigest()
    checksum_fields = local_checksum.decode("ascii").split()
    if not checksum_fields or checksum_fields[0].lower() != expected_sha1:
        raise ValueError("local SHA1 asset does not match the signed archive")

    assets = {asset.get("name"): asset for asset in release.get("assets", [])}
    expected_names = (Path(archive_path).name, Path(checksum_path).name)
    for name in expected_names:
        asset = assets.get(name)
        if not asset or asset.get("state") != "uploaded" or not asset.get("browser_download_url"):
            raise ValueError(f"release is missing uploaded public asset {name}")
        remote_data = fetch(asset["browser_download_url"])
        expected_data = local_archive if name == expected_names[0] else local_checksum
        if remote_data != expected_data:
            raise ValueError(f"public release asset does not match local signed build: {name}")

    return int(release["id"])


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: verify_public_release_assets.py OWNER/REPO TAG ARCHIVE SHA1")
    try:
        print(verify(*sys.argv[1:]))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, HTTPError, URLError) as error:
        raise SystemExit(f"public release asset verification failed: {error}") from error
