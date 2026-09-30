#!/usr/bin/env python3
"""Check plugin archive structure, version, and signed-manifest envelope."""

import json
import re
import stat
import sys
import zipfile


SIGNED_BEGIN = b"-----BEGIN PGP SIGNED MESSAGE-----"
SIGNATURE_BEGIN = b"-----BEGIN PGP SIGNATURE-----"
SIGNATURE_END = b"-----END PGP SIGNATURE-----"


def verify(archive_path: str, plugin_id: str, tag: str, require_signature: str = "true") -> None:
    if require_signature not in ("true", "false"):
        raise ValueError("REQUIRE_SIGNATURE must be true or false")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", plugin_id):
        raise ValueError("invalid plugin ID")
    expected_version = tag.removeprefix("v")
    manifest_path = f"{plugin_id}/MANIFEST.txt"
    metadata_path = f"{plugin_id}/plugin.json"

    with zipfile.ZipFile(archive_path) as archive:
        names = set()
        for entry in archive.infolist():
            name = entry.filename
            if name in names:
                raise ValueError(f"duplicate archive entry: {name}")
            names.add(name)
            parts = name.removesuffix("/").split("/")
            if parts[0] != plugin_id or any(part in ("", ".", "..") for part in parts) or "\\" in name:
                raise ValueError(f"unsafe archive path: {name}")
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError(f"unsupported archive entry: {name}")
        if metadata_path not in names:
            raise ValueError(f"archive is missing {metadata_path}")
        metadata = json.loads(archive.read(metadata_path))
        manifest = archive.read(manifest_path) if manifest_path in names else None

    if metadata.get("id") != plugin_id:
        raise ValueError("plugin ID does not match archive root")
    if metadata.get("info", {}).get("version") != expected_version:
        raise ValueError("plugin version does not match release tag")

    if require_signature == "false":
        return

    if manifest is None:
        raise ValueError(f"archive is missing {manifest_path}")
    if not manifest.startswith(SIGNED_BEGIN):
        raise ValueError("MANIFEST.txt is not an armored PGP signed message")
    if SIGNATURE_BEGIN not in manifest or SIGNATURE_END not in manifest:
        raise ValueError("MANIFEST.txt has no complete PGP signature block")
    if manifest.index(SIGNATURE_BEGIN) >= manifest.index(SIGNATURE_END):
        raise ValueError("MANIFEST.txt has malformed PGP signature block")

    try:
        lines = manifest.replace(b"\r\n", b"\n").split(b"\n")
        if lines[0] != SIGNED_BEGIN:
            raise ValueError("invalid signed-message delimiter")
        payload_start = lines.index(b"", 1) + 1
        signature_start = lines.index(SIGNATURE_BEGIN, payload_start)
        lines.index(SIGNATURE_END, signature_start + 1)
        payload = b"\n".join(
            line.removeprefix(b"- ") for line in lines[payload_start:signature_start]
        )
        signed_metadata = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("MANIFEST.txt has malformed clear-signed JSON payload") from error
    if not isinstance(signed_metadata, dict) or signed_metadata.get("signatureType") not in (
        "grafana", "commercial", "community"
    ):
        raise ValueError("MANIFEST.txt must declare a public Grafana signature type")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: verify_release_archive.py ARCHIVE PLUGIN_ID TAG REQUIRE_SIGNATURE")
    try:
        verify(*sys.argv[1:])
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise SystemExit(f"release archive verification failed: {error}") from error
