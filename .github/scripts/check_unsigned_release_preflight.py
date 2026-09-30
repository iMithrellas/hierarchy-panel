#!/usr/bin/env python3
"""Prevent unsigned release runs from mutating a published stable release."""

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def check(repository: str, tag: str, token: str) -> str:
    if not token:
        raise ValueError("GH_TOKEN is required for release preflight")

    url = f"https://api.github.com/repos/{repository}/releases/tags/{quote(tag, safe='')}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "hierarchy-timeline-release-preflight",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            release = json.loads(response.read())
    except HTTPError as error:
        with error:
            if error.code == 404:
                return "no existing published release"
            raise RuntimeError(f"GitHub release preflight failed with HTTP {error.code}") from None
    except URLError as error:
        raise RuntimeError("GitHub release preflight request failed") from None

    if not isinstance(release.get("draft"), bool) or not isinstance(release.get("prerelease"), bool):
        raise RuntimeError("GitHub release preflight returned incomplete release state")
    if not release["draft"] and not release["prerelease"]:
        raise RuntimeError("refusing unsigned run: this tag already has a published stable release")
    return "existing release is not stable"


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_unsigned_release_preflight.py OWNER/REPO TAG")
    try:
        print(check(sys.argv[1], sys.argv[2], os.environ.get("GH_TOKEN", "")))
    except (ValueError, RuntimeError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
