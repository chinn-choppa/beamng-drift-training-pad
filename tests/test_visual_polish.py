from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_visual_polish as polish
import generate_level
import generate_preview
import package_mod


class VisualPolishTests(unittest.TestCase):
    def make_tree(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        generate_level.generate(root)
        generate_preview.generate(root)
        self.assertTrue(polish.apply(root))
        return root

    def test_apply_is_idempotent_and_checkable(self):
        root = self.make_tree()
        first = (root / polish.MISSION_ITEMS).read_bytes()
        self.assertTrue(polish.apply(root, check=True))
        self.assertTrue(polish.apply(root))
        self.assertEqual(first, (root / polish.MISSION_ITEMS).read_bytes())

    def test_generated_collada_assets_parse(self):
        for text in (
            polish.build_graphics_dae(),
            polish.build_boundaries_dae(),
            polish.build_cone_dae(),
            polish.build_scenery_dae(),
        ):
            root = ET.fromstring(text)
            self.assertTrue(root.tag.endswith("COLLADA"))
            tri = root.find(".//{http://www.collada.org/2005/11/COLLADASchema}triangles")
            self.assertIsNotNone(tri)
            self.assertGreater(int(tri.attrib["count"]), 0)

    def test_asphalt_textures_are_deterministic_png(self):
        for builder in (polish.build_asphalt_base_png, polish.build_asphalt_roughness_png):
            a = builder()
            b = builder()
            self.assertEqual(a, b)
            self.assertEqual(a[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", a[16:24]), (256, 256))

    def test_asphalt_visuals_preserve_stock_physics_class(self):
        root = self.make_tree()
        materials = json.loads((root / polish.MATERIALS).read_text(encoding="utf-8"))
        asphalt = materials[polish.ASPHALT_MATERIAL]
        self.assertEqual(asphalt["groundType"], "ASPHALT")
        stage = asphalt["Stages"][0]
        self.assertEqual(stage["baseColorMap"], f"/{polish.ASPHALT_BASE_TEXTURE.as_posix()}")
        self.assertEqual(stage["roughnessMap"], f"/{polish.ASPHALT_ROUGHNESS_TEXTURE.as_posix()}")
        self.assertFalse((root / polish.LEVEL_ROOT / "groundModels").exists())

    def test_training_graphics_and_cones_are_non_colliding(self):
        root = self.make_tree()
        objects = [json.loads(line) for line in (root / polish.MISSION_ITEMS).read_text(encoding="utf-8").splitlines()]
        by_name = {obj.get("name"): obj for obj in objects}
        self.assertEqual(by_name[polish.GRAPHICS_MESH_NAME]["collisionType"], "None")
        self.assertEqual(by_name[polish.SCENERY_MESH_NAME]["collisionType"], "None")
        cones = [obj for obj in objects if obj.get("shapeName") == polish.CONE_MESH_PATH]
        self.assertGreaterEqual(len(cones), 14)
        self.assertTrue(all(obj["collisionType"] == "None" for obj in cones))

    def test_only_perimeter_presentation_mesh_is_colliding(self):
        root = self.make_tree()
        objects = [json.loads(line) for line in (root / polish.MISSION_ITEMS).read_text(encoding="utf-8").splitlines()]
        boundary = [obj for obj in objects if obj.get("name") == polish.BOUNDARY_MESH_NAME]
        self.assertEqual(len(boundary), 1)
        self.assertEqual(boundary[0]["collisionType"], "Visible Mesh")

    def test_zone_labels_use_supported_font(self):
        for _, label, _ in polish.ZONE_SPECS:
            for ch in label:
                self.assertTrue(ch == " " or ch in polish.FONT_5X7, ch)

    def test_packaged_zip_contains_visual_polish_assets(self):
        root = self.make_tree()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mod.zip"
            package_mod.package(root, out)
            with zipfile.ZipFile(out) as archive:
                names = set(archive.namelist())
            for rel in (
                polish.GRAPHICS_DAE,
                polish.BOUNDARIES_DAE,
                polish.CONE_DAE,
                polish.SCENERY_DAE,
                polish.ASPHALT_BASE_TEXTURE,
                polish.ASPHALT_ROUGHNESS_TEXTURE,
            ):
                self.assertIn(rel.as_posix(), names)

    def test_polished_package_is_deterministic(self):
        root = self.make_tree()
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.zip", Path(tmp) / "b.zip"
            package_mod.package(root, a)
            package_mod.package(root, b)
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(digest(a), digest(b))


if __name__ == "__main__":
    unittest.main()
