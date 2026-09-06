from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = load_module("generate_level_runtime", ROOT / "scripts" / "generate_level.py")
validator = load_module("validate_level_runtime", ROOT / "scripts" / "validate_level.py")
preview = load_module("generate_preview_runtime", ROOT / "scripts" / "generate_preview.py")


class RuntimeMarkingFallbackTests(unittest.TestCase):
    def make_tree(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        gen.generate(root)
        preview.generate(root)
        return root

    def test_visual_marking_mesh_is_collision_free(self):
        meshes = [o for o in gen.build_objects() if o.get("name") == gen.MARKING_MESH_NAME]
        self.assertEqual(len(meshes), 1)
        mesh = meshes[0]
        self.assertEqual(mesh["class"], "TSStatic")
        self.assertEqual(mesh["shapeName"], gen.MARKING_MESH_PATH)
        self.assertEqual(mesh["collisionType"], "None")
        self.assertEqual(mesh["decalType"], "None")
        self.assertTrue(mesh["isRenderEnabled"])

    def test_markings_dae_contains_renderable_triangles(self):
        root = ET.fromstring(gen.build_markings_dae())
        ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
        triangles = root.find(".//c:triangles", ns)
        self.assertIsNotNone(triangles)
        self.assertGreater(int(triangles.attrib["count"]), 1000)
        materials = {m.attrib.get("name") for m in root.findall(".//c:material", ns)}
        self.assertIn(gen.MARKING_MATERIAL, materials)

    def test_environment_avoids_known_smoke_test_errors(self):
        objects = gen.build_objects()
        infos = [o for o in objects if o.get("class") == "LevelInfo"]
        self.assertEqual(len(infos), 1)
        self.assertEqual(infos[0]["globalEnviromentMap"], "DefaultSkyCubemap")
        self.assertFalse(any(o.get("class") == "CloudLayer" for o in objects))

    def test_generated_mesh_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            aroot, broot = Path(a), Path(b)
            gen.generate(aroot)
            gen.generate(broot)
            self.assertEqual((aroot / gen.MARKINGS_DAE).read_bytes(), (broot / gen.MARKINGS_DAE).read_bytes())

    def test_validator_rejects_missing_visual_mesh(self):
        root = self.make_tree()
        (root / gen.MARKINGS_DAE).unlink()
        errors = validator.validate(root)
        self.assertTrue(any("training_markings.dae" in error for error in errors), errors)

    def test_validator_rejects_collidable_markings(self):
        root = self.make_tree()
        path = root / gen.MISSION_ITEMS
        objects = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        for obj in objects:
            if obj.get("name") == gen.MARKING_MESH_NAME:
                obj["collisionType"] = "Visible Mesh"
        path.write_text("".join(json.dumps(obj) + "\n" for obj in objects), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("collisionType must be None" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
