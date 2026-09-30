import io
import json
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from check_unsigned_release_preflight import check


def response(payload):
    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    return Response(json.dumps(payload).encode())


class UnsignedReleasePreflightTest(unittest.TestCase):
    def test_allows_missing_release_404_as_initial_submission(self):
        body = io.BytesIO(b"Not Found")
        error = HTTPError("https://api.github.test", 404, "Not Found", {}, body)
        with patch("check_unsigned_release_preflight.urlopen", side_effect=error) as request:
            self.assertEqual(check("acme/plugin", "v1.2.3", "secret"), "no existing published release")
            self.assertEqual(request.call_args.args[0].get_header("Authorization"), "Bearer secret")
        self.assertTrue(body.closed)

    def test_allows_existing_prerelease(self):
        with patch("check_unsigned_release_preflight.urlopen", return_value=response({"draft": False, "prerelease": True})):
            self.assertEqual(check("acme/plugin", "v1.2.3", "secret"), "existing release is not stable")

    def test_refuses_published_stable_release(self):
        with patch("check_unsigned_release_preflight.urlopen", return_value=response({"draft": False, "prerelease": False})):
            with self.assertRaisesRegex(RuntimeError, "refusing unsigned run"):
                check("acme/plugin", "v1.2.3", "secret")

    def test_fails_closed_on_non_404_api_error(self):
        body = io.BytesIO(b"Unavailable")
        error = HTTPError("https://api.github.test", 503, "Unavailable", {}, body)
        with patch("check_unsigned_release_preflight.urlopen", side_effect=error):
            with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
                check("acme/plugin", "v1.2.3", "secret")
        self.assertTrue(body.closed)

    def test_closes_http_errors_without_response_body(self):
        for code in (404, 503):
            with self.subTest(code=code):
                error = HTTPError("https://api.github.test", code, "Failure", {}, None)
                with patch("check_unsigned_release_preflight.urlopen", side_effect=error):
                    if code == 404:
                        self.assertEqual(check("acme/plugin", "v1.2.3", "secret"), "no existing published release")
                    else:
                        with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
                            check("acme/plugin", "v1.2.3", "secret")
                self.assertTrue(error.closed)

    def test_fails_closed_when_release_state_is_malformed(self):
        with patch("check_unsigned_release_preflight.urlopen", return_value=response({"draft": False})):
            with self.assertRaisesRegex(RuntimeError, "incomplete release state"):
                check("acme/plugin", "v1.2.3", "secret")


if __name__ == "__main__":
    unittest.main()
