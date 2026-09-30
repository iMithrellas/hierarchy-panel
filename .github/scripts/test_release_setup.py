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

    def test_signed_release_requires_strict_signature_before_upload(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text()
        step = re.search(
            r"      - name: Require valid public Grafana signature\n(.*?)(?=      -)",
            workflow,
            re.DOTALL,
        )
        self.assertIsNotNone(step)
        self.assertIn("steps.signing.outputs.enabled == 'true'", step.group(1))
        self.assertIn('-analyzer signature -strict "$PLUGIN_ARCHIVE"', step.group(1))
        self.assertLess(step.start(), workflow.index("softprops/action-gh-release"))
        self.assertLess(step.start(), workflow.index("Promote verified signed release to stable"))

    def test_same_tag_release_runs_are_serialized(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn("concurrency:\n  group: release-${{ github.ref }}\n  cancel-in-progress: false", workflow)

    def test_release_regressions_run_in_ci_and_release(self):
        for name in ("ci.yml", "release.yml"):
            with self.subTest(workflow=name):
                workflow = (ROOT / ".github/workflows" / name).read_text()
                self.assertIn("python3 -m unittest discover -s .github/scripts -v", workflow)


if __name__ == "__main__":
    unittest.main()
