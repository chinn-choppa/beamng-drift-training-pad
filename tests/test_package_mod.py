from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import package_mod
import generate_level
import generate_preview


class PackageTests(unittest.TestCase):
    def stage(self, root: Path) -> None:
        generate_level.generate(root)
        generate_preview.generate(root)

    def test_zip_has_beamng_level_at_archive_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage_root = Path(tmp) / "repo"
            self.stage(stage_root)
            out = Path(tmp) / "mod.zip"
            package_mod.package(stage_root, out)
            with zipfile.ZipFile(out) as archive:
                names = archive.namelist()
            self.assertIn("levels/drift_training_pad/info.json", names)
            self.assertIn("levels/drift_training_pad/main/items.level.json", names)
            self.assertIn("levels/drift_training_pad/preview.png", names)
            self.assertTrue(all(name.startswith("levels/drift_training_pad/") for name in names))
            self.assertFalse(any(name.startswith("beamng-drift-training-pad/") for name in names))

    def test_zip_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage_root = Path(tmp) / "repo"
            self.stage(stage_root)
            first = Path(tmp) / "first.zip"
            second = Path(tmp) / "second.zip"
            package_mod.package(stage_root, first)
            package_mod.package(stage_root, second)
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(digest(first), digest(second))


if __name__ == "__main__":
    unittest.main()
