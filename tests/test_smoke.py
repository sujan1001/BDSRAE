import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SmokePipelineTest(unittest.TestCase):
    def test_pipeline_writes_expected_outputs(self):
        output = ROOT / "results" / "test-run"
        command = [sys.executable, "scripts/run_pipeline.py", "--config", "configs/smoke.json", "--output", str(output)]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertIn("languages", completed.stdout)
        self.assertTrue((output / "metrics.csv").exists())
        manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["responsible_ai"]["personal_data_used"])
        self.assertEqual(set(manifest["data_validation"]["languages"]), {"en", "hi", "ml"})


if __name__ == "__main__":
    unittest.main()

