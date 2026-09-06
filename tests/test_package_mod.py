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


class PackageTests(unittest.TestCase):
    def test_zip_has_beamng_level_at_archive_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mod.zip"
            package_mod.package(ROOT, out)
            with zipfile.ZipFile(out) as archive:
                names = archive.namelist()
            self.assertIn("levels/drift_training_pad/info.json", names)
            self.assertIn("levels/drift_training_pad/main/items.level.json", names)
            self.assertIn("levels/drift_training_pad/preview.png", names)
            self.assertTrue(all(name.startswith("levels/drift_training_pad/") for name in names))
            self.assertFalse(any(name.startswith("beamng-drift-training-pad/") for name in names))

    def test_zip_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.zip"
            second = Path(tmp) / "second.zip"
            package_mod.package(ROOT, first)
            package_mod.package(ROOT, second)
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(digest(first), digest(second))


if __name__ == "__main__":
    unittest.main()
