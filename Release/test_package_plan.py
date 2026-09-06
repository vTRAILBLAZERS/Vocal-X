import json
import tempfile
import unittest
from pathlib import Path
from package_plan import plan, contained

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ("Release", "Pipelines/Presets", "App", "Private"):
            (self.root / folder).mkdir(parents=True)
        (self.root / "Release/model-rights-audit.json").write_text('{"models": []}')
        (self.root / "App/vocal_gui.py").write_text('print("gui")')
        (self.root / "App/test_license_fixture.py").write_text("secret fixture")
        (self.root / "Private/key.pem").write_text("secret key")

    def sources(self):
        return {f["source"] for f in plan(self.root)["files"]}

    def test_secrets_excluded_and_live_unknown_model_blocked(self):
        (self.root / "Pipelines/Presets/new.json").write_text(json.dumps({
            "name": "New",
            "stages": [{"enabled": True, "model": "unknown"}],
        }))
        result = plan(self.root)
        self.assertEqual(result["presets"][0]["blocked_models"], ["unknown"])
        sources = {f["source"] for f in result["files"]}
        self.assertIn("App/vocal_gui.py", sources)
        self.assertIn("Pipelines/Presets/new.json", sources)
        self.assertNotIn("Private/key.pem", sources)
        self.assertNotIn("App/test_license_fixture.py", sources)
        self.assertFalse(result["release_ready"])

    def test_changed_payload_changes_hash(self):
        before = next(f["sha256"] for f in plan(self.root)["files"] if f["source"] == "App/vocal_gui.py")
        (self.root / "App/vocal_gui.py").write_text('print("changed")')
        after = next(f["sha256"] for f in plan(self.root)["files"] if f["source"] == "App/vocal_gui.py")
        self.assertNotEqual(before, after)

    def test_runtime_support_payload_included(self):
        config = self.root / "Config/core-model-download-report.json"
        source360 = self.root / "Tools/AnyEnhance-360M-Recovered/models/se/anyenhance/modules/encoder_loss.py"
        sourcev1 = self.root / "Tools/AnyEnhance-v1/anyenhance/__init__.py"
        configv1 = self.root / "Tools/AnyEnhance-v1/config/anyenhance_v1.json"
        for path in (config, source360, sourcev1, configv1):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("payload")
        sources = self.sources()
        self.assertIn("Config/core-model-download-report.json", sources)
        self.assertIn("Tools/AnyEnhance-360M-Recovered/models/se/anyenhance/modules/encoder_loss.py", sources)
        self.assertIn("Tools/AnyEnhance-v1/anyenhance/__init__.py", sources)
        self.assertIn("Tools/AnyEnhance-v1/config/anyenhance_v1.json", sources)
        self.assertFalse(any(s.startswith("Models/") for s in sources))

    def test_escape_rejected(self):
        with self.assertRaises(ValueError):
            contained(self.root, "../outside")

if __name__ == "__main__":
    unittest.main(verbosity=2)
