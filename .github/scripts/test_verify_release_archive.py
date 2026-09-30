import json
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys
import warnings
import stat

sys.path.insert(0, str(Path(__file__).parent))
from verify_release_archive import verify


SIGNED_MANIFEST = b"""-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

{
  "manifestVersion": "2.0.0",
  "signatureType": "community",
  "signedByOrg": "example",
  "signedByOrgName": "Example",
  "plugin": "example-plugin",
  "version": "1.2.3",
  "time": 1773149886162,
  "keyId": "7e4d0c6a708866e7",
  "files": {"plugin.json": "0000000000000000000000000000000000000000000000000000000000000000"}
}
-----BEGIN PGP SIGNATURE-----

iQIzBAABCAAdFiEEexample
-----END PGP SIGNATURE-----
"""


class VerifyReleaseArchiveTest(unittest.TestCase):
    def archive(self, manifest=SIGNED_MANIFEST, version="1.2.3"):
        temporary = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("example-plugin/MANIFEST.txt", manifest)
            archive.writestr(
                "example-plugin/plugin.json",
                json.dumps({"id": "example-plugin", "info": {"version": version}}),
            )
        self.addCleanup(path.unlink, missing_ok=True)
        return str(path)

    def test_accepts_signed_manifest_and_matching_tag(self):
        verify(self.archive(), "example-plugin", "v1.2.3")

    def test_accepts_public_signature_types(self):
        for signature_type in ("grafana", "commercial", "community"):
            with self.subTest(signature_type=signature_type):
                manifest = SIGNED_MANIFEST.replace(b'"community"', json.dumps(signature_type).encode())
                verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_rejects_non_public_signature_types(self):
        for signature_type in ("private", "private-glob", "unknown", "", None, [], {}):
            with self.subTest(signature_type=signature_type):
                manifest = SIGNED_MANIFEST.replace(b'"community"', json.dumps(signature_type).encode())
                with self.assertRaisesRegex(ValueError, "public Grafana signature type"):
                    verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_rejects_missing_signature_type(self):
        manifest = SIGNED_MANIFEST.replace(b'  "signatureType": "community",\n', b'')
        with self.assertRaisesRegex(ValueError, "public Grafana signature type"):
            verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_rejects_malformed_payload(self):
        for payload in (b'not JSON', b'{', b'', b'\xff'):
            with self.subTest(payload=payload):
                header, body = SIGNED_MANIFEST.split(b'\n\n', 1)
                _, signature = body.split(b'-----BEGIN PGP SIGNATURE-----', 1)
                manifest = header + b'\n\n' + payload + b'\n-----BEGIN PGP SIGNATURE-----' + signature
                with self.assertRaisesRegex(ValueError, "malformed clear-signed JSON payload"):
                    verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_rejects_non_object_payload(self):
        for payload in (b'null', b'[]', b'"community"', b'42'):
            with self.subTest(payload=payload):
                header, body = SIGNED_MANIFEST.split(b'\n\n', 1)
                _, signature = body.split(b'-----BEGIN PGP SIGNATURE-----', 1)
                manifest = header + b'\n\n' + payload + b'\n-----BEGIN PGP SIGNATURE-----' + signature
                with self.assertRaisesRegex(ValueError, "public Grafana signature type"):
                    verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_accepts_crlf_and_mixed_line_endings(self):
        header, body = SIGNED_MANIFEST.split(b'\n\n', 1)
        for manifest in (
            SIGNED_MANIFEST.replace(b'\n', b'\r\n'),
            header + b'\n\n' + body.replace(b'\n', b'\r\n'),
        ):
            with self.subTest(manifest=manifest):
                verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_accepts_dash_escaped_cleartext(self):
        manifest = SIGNED_MANIFEST.replace(b'  "time": 1773149886162,', b'  "time":\n- -1773149886162,')
        verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_rejects_missing_armor_header_separator(self):
        manifest = SIGNED_MANIFEST.replace(b'Hash: SHA512\n\n', b'Hash: SHA512\n')
        with self.assertRaisesRegex(ValueError, "malformed clear-signed JSON payload"):
            verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_rejects_unsigned_manifest(self):
        with self.assertRaisesRegex(ValueError, "not an armored PGP"):
            verify(self.archive(b"unsigned manifest"), "example-plugin", "v1.2.3")

    def test_allows_unsigned_submission_archive_without_manifest(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("example-plugin/plugin.json", '{"id":"example-plugin","info":{"version":"1.2.3"}}')
        self.addCleanup(path.unlink, missing_ok=True)
        verify(str(path), "example-plugin", "v1.2.3", "false")

    def test_rejects_missing_manifest_from_archive(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("example-plugin/plugin.json", '{"id":"example-plugin","info":{"version":"1.2.3"}}')
        self.addCleanup(path.unlink, missing_ok=True)
        with self.assertRaisesRegex(ValueError, "missing example-plugin/MANIFEST.txt"):
            verify(str(path), "example-plugin", "v1.2.3")

    def test_rejects_version_mismatch(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify(self.archive(version="1.2.2"), "example-plugin", "v1.2.3")

    def test_rejects_incomplete_pgp_signature_block(self):
        manifest = SIGNED_MANIFEST.replace(b"-----END PGP SIGNATURE-----", b"")
        with self.assertRaisesRegex(ValueError, "complete PGP signature"):
            verify(self.archive(manifest), "example-plugin", "v1.2.3")

    def test_rejects_invalid_signature_requirement(self):
        for requirement in ("", "TRUE", "tru", "1"):
            with self.subTest(requirement=requirement), self.assertRaisesRegex(ValueError, "must be true or false"):
                verify(self.archive(), "example-plugin", "v1.2.3", requirement)

    def test_rejects_metadata_id_mismatch(self):
        with self.assertRaisesRegex(ValueError, "plugin ID does not match"):
            path = self.archive()
            with zipfile.ZipFile(path, "r") as source:
                entries = {name: source.read(name) for name in source.namelist()}
            entries["example-plugin/plugin.json"] = b'{"id":"other-plugin","info":{"version":"1.2.3"}}'
            with zipfile.ZipFile(path, "w") as archive:
                for name, contents in entries.items():
                    archive.writestr(name, contents)
            verify(path, "example-plugin", "v1.2.3")

    def test_rejects_duplicate_entries(self):
        path = self.archive()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("example-plugin/plugin.json", '{}')
        with self.assertRaisesRegex(ValueError, "duplicate archive entry"):
            verify(path, "example-plugin", "v1.2.3")

    def test_rejects_unsafe_paths(self):
        for name in ("../escape", "example-plugin/../escape", "example-plugin/./module.js", "example-plugin//module.js", "example-plugin\\module.js", "/example-plugin/module.js", "other-plugin/module.js"):
            with self.subTest(name=name):
                path = self.archive()
                with zipfile.ZipFile(path, "a") as archive:
                    archive.writestr(name, b"module")
                with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                    verify(path, "example-plugin", "v1.2.3")

    def test_rejects_double_trailing_slash(self):
        for name in ("example-plugin//", "example-plugin/foo//"):
            with self.subTest(name=name):
                path = self.archive()
                with zipfile.ZipFile(path, "a") as archive:
                    archive.writestr(name, b"")
                with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                    verify(path, "example-plugin", "v1.2.3")

    def test_accepts_legitimate_directory_entries(self):
        path = self.archive()
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr("example-plugin/", b"")
            archive.writestr("example-plugin/foo/", b"")
        verify(path, "example-plugin", "v1.2.3")

    def test_rejects_symlinks(self):
        path = self.archive()
        link = zipfile.ZipInfo("example-plugin/module.js")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr(link, "../../module.js")
        with self.assertRaisesRegex(ValueError, "unsupported archive entry"):
            verify(path, "example-plugin", "v1.2.3")


if __name__ == "__main__":
    unittest.main()
