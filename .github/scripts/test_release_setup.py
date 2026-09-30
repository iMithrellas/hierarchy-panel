import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ReleaseSetupTest(unittest.TestCase):
    def test_packaging_action_has_locked_sign_command(self):
        package = json.loads((ROOT / "package.json").read_text())
        lock = json.loads((ROOT / "package-lock.json").read_text())
        self.assertEqual(package["scripts"]["sign"], "sign-plugin")
        version = package["devDependencies"]["@grafana/sign-plugin"]
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertEqual(lock["packages"][""]["devDependencies"]["@grafana/sign-plugin"], version)
        signer = lock["packages"]["node_modules/@grafana/sign-plugin"]
        self.assertEqual(signer["version"], version)
        self.assertIn("sign-plugin", signer["bin"])


if __name__ == "__main__":
    unittest.main()
