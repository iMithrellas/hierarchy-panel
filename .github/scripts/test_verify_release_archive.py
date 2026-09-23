import json
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from verify_release_archive import verify


SIGNED_MANIFEST = b"""-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA256

Grafana plugin manifest contents
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
                json.dumps({"info": {"version": version}}),
            )
        self.addCleanup(path.unlink, missing_ok=True)
        return str(path)

    def test_accepts_signed_manifest_and_matching_tag(self):
        verify(self.archive(), "example-plugin", "v1.2.3")

    def test_rejects_unsigned_manifest(self):
        with self.assertRaisesRegex(ValueError, "not an armored PGP"):
            verify(self.archive(b"unsigned manifest"), "example-plugin", "v1.2.3")

    def test_allows_unsigned_submission_archive_without_manifest(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("example-plugin/plugin.json", '{"info":{"version":"1.2.3"}}')
        self.addCleanup(path.unlink, missing_ok=True)
        verify(str(path), "example-plugin", "v1.2.3", "false")

    def test_rejects_missing_manifest_from_archive(self):
        temporary = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("example-plugin/plugin.json", '{"info":{"version":"1.2.3"}}')
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


if __name__ == "__main__":
    unittest.main()
