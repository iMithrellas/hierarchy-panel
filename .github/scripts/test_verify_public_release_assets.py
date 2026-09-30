import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parent))
from verify_public_release_assets import fetch, verify


class FetchTest(unittest.TestCase):
    def test_closes_http_error_bodies_and_preserves_exception(self):
        for code in (404, 503):
            with self.subTest(code=code):
                body = io.BytesIO(b"Failure")
                error = HTTPError("https://public/archive", code, "Failure", {}, body)
                with patch("verify_public_release_assets.urlopen", side_effect=error):
                    with self.assertRaises(HTTPError) as raised:
                        fetch("https://public/archive")
                self.assertIs(raised.exception, error)
                self.assertTrue(body.closed)

    def test_closes_http_errors_without_response_body(self):
        error = HTTPError("https://public/archive", 503, "Failure", {}, None)
        with patch("verify_public_release_assets.urlopen", side_effect=error):
            with self.assertRaises(HTTPError) as raised:
                fetch("https://public/archive")
        self.assertIs(raised.exception, error)
        self.assertTrue(error.closed)


class VerifyPublicReleaseAssetsTest(unittest.TestCase):
    def setUp(self):
        self.archive = b"signed plugin zip fixture"
        self.checksum = (hashlib.sha1(self.archive).hexdigest() + "\n").encode()
        self.temp = tempfile.TemporaryDirectory()
        self.archive_path = Path(self.temp.name) / "plugin-1.2.3.zip"
        self.checksum_path = Path(self.temp.name) / "plugin-1.2.3.zip.sha1"
        self.archive_path.write_bytes(self.archive)
        self.checksum_path.write_bytes(self.checksum)
        self.release = {
            "id": 8675309,
            "draft": False,
            "prerelease": True,
            "assets": [
                {"name": self.archive_path.name, "state": "uploaded", "browser_download_url": "https://public/archive"},
                {"name": self.checksum_path.name, "state": "uploaded", "browser_download_url": "https://public/sha1"},
            ],
        }

    def tearDown(self):
        self.temp.cleanup()

    def run_verify(self, remote_archive=None, remote_checksum=None):
        responses = {
            "https://api.github.com/repos/acme/plugin/releases/tags/v1.2.3": json.dumps(self.release).encode(),
            "https://public/archive": self.archive if remote_archive is None else remote_archive,
            "https://public/sha1": self.checksum if remote_checksum is None else remote_checksum,
        }
        with patch("verify_public_release_assets.fetch", side_effect=lambda url: responses[url]):
            return verify("acme/plugin", "v1.2.3", str(self.archive_path), str(self.checksum_path))

    def test_accepts_matching_public_signed_assets(self):
        self.assertEqual(self.run_verify(), 8675309)

    def test_rejects_release_that_is_not_kept_prerelease(self):
        self.release["prerelease"] = False
        with self.assertRaisesRegex(ValueError, "remain a published prerelease"):
            self.run_verify()

    def test_rejects_public_archive_mismatch(self):
        with self.assertRaisesRegex(ValueError, "does not match local signed build"):
            self.run_verify(remote_archive=b"unsigned or stale zip")

    def test_rejects_missing_uploaded_checksum(self):
        self.release["assets"].pop()
        with self.assertRaisesRegex(ValueError, "missing uploaded public asset"):
            self.run_verify()


if __name__ == "__main__":
    unittest.main()
