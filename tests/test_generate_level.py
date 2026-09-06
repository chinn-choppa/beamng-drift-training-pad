from __future__ import annotations

import importlib.util
import math
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


gen = load_module("generate_level", ROOT / "scripts" / "generate_level.py")


class GenerateLevelTests(unittest.TestCase):
    def test_generation_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            aroot, broot = Path(a), Path(b)
            self.assertTrue(gen.generate(aroot))
            self.assertTrue(gen.generate(broot))
            for rel in (gen.SCENE_ROOT, gen.MISSION_ITEMS, gen.MATERIALS, gen.INFO):
                self.assertEqual((aroot / rel).read_bytes(), (broot / rel).read_bytes(), rel)

    def test_committed_generated_files_are_current(self):
        self.assertTrue(gen.generate(ROOT, check=True))

    def test_required_spawns_are_unique(self):
        objects = gen.build_objects()
        spawns = [o for o in objects if o.get("class") == "SpawnSphere"]
        names = [o["name"] for o in spawns]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            set(names),
            {
                "spawns_default", "spawns_donut", "spawns_large_circle",
                "spawns_figure_eight_easy", "spawns_figure_eight_normal",
                "spawns_transition_lane", "spawns_single_corner", "spawns_training_loop",
            },
        )

    def test_donut_and_large_circle_radii(self):
        roads = {o["name"]: o for o in gen.build_objects() if o.get("class") == "DecalRoad"}
        for prefix, center, radii in [
            ("donut_ring", (-185.0, 150.0), (8, 10, 12)),
            ("large_circle", (65.0, 150.0), (15, 20, 25)),
        ]:
            for radius in radii:
                road = roads[f"{prefix}_{radius}m"]
                self.assertTrue(road["looped"])
                measured = [
                    math.hypot(node[0] - center[0], node[1] - center[1])
                    for node in road["nodes"]
                ]
                self.assertLess(max(abs(value - radius) for value in measured), 0.001)

    def test_figure_eights_cross_their_centers(self):
        roads = {o["name"]: o for o in gen.build_objects() if o.get("class") == "DecalRoad"}
        for name, center in [
            ("figure_eight_easy", (-155, -85)),
            ("figure_eight_normal", (45, -85)),
        ]:
            road = roads[name]
            self.assertTrue(road["looped"])
            min_dist = min(math.hypot(p[0] - center[0], p[1] - center[1]) for p in road["nodes"])
            self.assertLess(min_dist, 0.001)

    def test_all_guides_are_non_drivable_asphalt_markings(self):
        objects = gen.build_objects()
        roads = [o for o in objects if o.get("class") == "DecalRoad"]
        self.assertGreaterEqual(len(roads), 20)
        for road in roads:
            self.assertEqual(road["material"], gen.MARKING_MATERIAL)
            self.assertEqual(road["drivability"], 0)
            self.assertTrue(road["overObjects"])
        materials = gen.build_materials()
        self.assertEqual(materials[gen.ASPHALT_MATERIAL]["groundType"], "ASPHALT")
        self.assertEqual(materials[gen.MARKING_MATERIAL]["groundType"], "ASPHALT")

    def test_info_exposes_every_spawn(self):
        info = gen.build_info()
        object_names = {entry["objectname"] for entry in info["spawnPoints"]}
        spawn_names = {o["name"] for o in gen.build_objects() if o.get("class") == "SpawnSphere"}
        self.assertEqual(object_names, spawn_names)
        self.assertIn(info["defaultSpawnPointName"], object_names)
        self.assertFalse(info["supportsTraffic"])


if __name__ == "__main__":
    unittest.main()
