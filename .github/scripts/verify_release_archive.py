#!/usr/bin/env python3
"""Check a packaged Grafana plugin's version and PGP-signed MANIFEST."""

import json
import sys
import zipfile


SIGNED_BEGIN = b"-----BEGIN PGP SIGNED MESSAGE-----"
SIGNATURE_BEGIN = b"-----BEGIN PGP SIGNATURE-----"
SIGNATURE_END = b"-----END PGP SIGNATURE-----"


def verify(archive_path: str, plugin_id: str, tag: str, require_signature: str = "true") -> None:
    expected_version = tag.removeprefix("v")
    manifest_path = f"{plugin_id}/MANIFEST.txt"
    metadata_path = f"{plugin_id}/plugin.json"

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        if metadata_path not in names:
            raise ValueError(f"archive is missing {metadata_path}")
        metadata = json.loads(archive.read(metadata_path))
        manifest = archive.read(manifest_path) if manifest_path in names else None

    if metadata.get("info", {}).get("version") != expected_version:
        raise ValueError("plugin version does not match release tag")

    if require_signature.lower() != "true":
        return

    if manifest is None:
        raise ValueError(f"archive is missing {manifest_path}")
    if not manifest.startswith(SIGNED_BEGIN):
        raise ValueError("MANIFEST.txt is not an armored PGP signed message")
    if SIGNATURE_BEGIN not in manifest or SIGNATURE_END not in manifest:
        raise ValueError("MANIFEST.txt has no complete PGP signature block")
    if manifest.index(SIGNATURE_BEGIN) >= manifest.index(SIGNATURE_END):
        raise ValueError("MANIFEST.txt has malformed PGP signature block")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: verify-release-archive.py ARCHIVE PLUGIN_ID TAG REQUIRE_SIGNATURE")
    try:
        verify(*sys.argv[1:])
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise SystemExit(f"release archive verification failed: {error}") from error
