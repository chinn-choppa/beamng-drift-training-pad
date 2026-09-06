from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = load_module("generate_level_for_validation", ROOT / "scripts" / "generate_level.py")
validator = load_module("validate_level", ROOT / "scripts" / "validate_level.py")


class ValidateLevelTests(unittest.TestCase):
    def make_tree(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        gen.generate(root)
        src_preview = ROOT / gen.LEVEL_ROOT / "preview.png"
        dst_preview = root / gen.LEVEL_ROOT / "preview.png"
        dst_preview.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_preview, dst_preview)
        return root

    def test_committed_level_passes(self):
        self.assertEqual(validator.validate(ROOT), [])

    def test_invalid_ndjson_is_rejected(self):
        root = self.make_tree()
        path = root / gen.MISSION_ITEMS
        path.write_text(path.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("invalid NDJSON" in error for error in errors), errors)

    def test_missing_default_spawn_is_rejected(self):
        root = self.make_tree()
        path = root / gen.INFO
        info = json.loads(path.read_text(encoding="utf-8"))
        info["defaultSpawnPointName"] = "spawns_missing"
        path.write_text(json.dumps(info), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("defaultSpawnPointName" in error for error in errors), errors)

    def test_non_asphalt_ground_material_is_rejected(self):
        root = self.make_tree()
        path = root / gen.MATERIALS
        materials = json.loads(path.read_text(encoding="utf-8"))
        materials[gen.ASPHALT_MATERIAL]["groundType"] = "ICE"
        path.write_text(json.dumps(materials), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("ASPHALT" in error for error in errors), errors)

    def test_missing_preview_is_rejected(self):
        root = self.make_tree()
        (root / gen.LEVEL_ROOT / "preview.png").unlink()
        errors = validator.validate(root)
        self.assertTrue(any("preview" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
