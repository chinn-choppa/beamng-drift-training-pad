from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

LEVEL_ID = "drift_training_pad"
LEVEL_ROOT = Path("levels") / LEVEL_ID
SCENE_ROOT = LEVEL_ROOT / "main" / "items.level.json"
MISSION_ITEMS = LEVEL_ROOT / "main" / "MissionGroup" / "items.level.json"
MATERIALS = LEVEL_ROOT / "main.materials.json"
INFO = LEVEL_ROOT / "info.json"

IDENTITY = [1, 0, 0, 0, 1, 0, 0, 0, 1]
MARKING_MATERIAL = "driftpad_marking_white"
ASPHALT_MATERIAL = "driftpad_asphalt"


def _round(value: float) -> float:
    return round(float(value), 4)


def _points_circle(cx: float, cy: float, radius: float, *, count: int = 72, z: float = 0.03, width: float = 0.18):
    return [
        [_round(cx + radius * math.cos(2 * math.pi * i / count)),
         _round(cy + radius * math.sin(2 * math.pi * i / count)),
         z, width]
        for i in range(count)
    ]


def _points_lemniscate(cx: float, cy: float, half_width: float, half_height: float, *, count: int = 96, z: float = 0.03, width: float = 0.22):
    points = []
    for i in range(count):
        t = 2 * math.pi * i / count
        x = cx + half_width * math.sin(t)
        y = cy + half_height * math.sin(t) * math.cos(t)
        points.append([_round(x), _round(y), z, width])
    return points


def _points_polyline(points: Iterable[tuple[float, float]], *, z: float = 0.03, width: float = 0.20):
    return [[_round(x), _round(y), z, width] for x, y in points]


def _arc(cx: float, cy: float, radius: float, start_deg: float, end_deg: float, *, count: int = 30, z: float = 0.03, width: float = 0.18):
    values = []
    for i in range(count):
        u = i / (count - 1)
        ang = math.radians(start_deg + (end_deg - start_deg) * u)
        values.append([_round(cx + radius * math.cos(ang)), _round(cy + radius * math.sin(ang)), z, width])
    return values


def decal_road(name: str, nodes: list[list[float]], *, looped: bool = False) -> dict:
    if len(nodes) < 2:
        raise ValueError(f"{name}: DecalRoad needs at least two nodes")
    first = nodes[0]
    obj = {
        "name": name,
        "class": "DecalRoad",
        "__parent": "MissionGroup",
        "position": [first[0], first[1], first[2]],
        "material": MARKING_MATERIAL,
        "nodes": nodes,
        "overObjects": True,
        "improvedSpline": True,
        "looped": looped,
        "renderPriority": 10,
        "drivability": 0,
    }
    return obj


def spawn(name: str, x: float, y: float, heading_deg: float = 0.0) -> dict:
    # BeamNG vehicles face +Y. Z-axis rotation matrix.
    angle = math.radians(heading_deg)
    c, s = _round(math.cos(angle)), _round(math.sin(angle))
    rot = [c, -s, 0, s, c, 0, 0, 0, 1]
    return {
        "class": "SpawnSphere",
        "name": name,
        "__parent": "MissionGroup",
        "position": [_round(x), _round(y), 0.6],
        "rotationMatrix": rot,
        "scale": [1, 1, 1],
        "dataBlock": "SpawnSphereMarker",
    }


def _cross(name: str, cx: float, cy: float, arm: float = 2.0) -> list[dict]:
    return [
        decal_road(f"{name}_x", _points_polyline([(cx - arm, cy), (cx + arm, cy)], width=0.12)),
        decal_road(f"{name}_y", _points_polyline([(cx, cy - arm), (cx, cy + arm)], width=0.12)),
    ]


def build_objects() -> list[dict]:
    objects: list[dict] = [
        {
            "name": "theLevelInfo",
            "class": "LevelInfo",
            "__parent": "MissionGroup",
            "gravity": -9.80665,
            "visibleDistance": 2500,
            "fogDensity": 0.00045,
            "fogAtmosphereHeight": 700,
        },
        {
            "name": "tod",
            "class": "TimeOfDay",
            "__parent": "MissionGroup",
            "startTime": 0,
            "time": 0,
            "play": False,
            "dayLength": 1200,
            "axisTilt": 23.44,
            "latitude": 48,
            "longitude": 11,
            "year": 2026,
            "month": 6,
            "day": 20,
            "utcOffset": "2",
            "celestialProfile": "earth",
        },
        {"name": "sunsky", "class": "ScatterSky", "__parent": "MissionGroup"},
        {
            "name": "clouds",
            "class": "CloudLayer",
            "__parent": "MissionGroup",
            "coverage": 0.12,
            "windSpeed": 0.02,
            "windDirection": [1, 0],
            "altitudeKm": 4,
        },
        {
            "name": "training_ground",
            "class": "GroundPlane",
            "__parent": "MissionGroup",
            "position": [0, 0, 0],
            "material": ASPHALT_MATERIAL,
            "squareSize": 16,
            "scaleU": 8,
            "scaleV": 8,
        },
    ]

    # Named spawn points near every exercise.
    objects.extend([
        spawn("spawns_default", 0, 270, 180),
        spawn("spawns_donut", -185, 205, 180),
        spawn("spawns_large_circle", 65, 205, 180),
        spawn("spawns_figure_eight_easy", -180, -5, 180),
        spawn("spawns_figure_eight_normal", 35, -5, 180),
        spawn("spawns_transition_lane", 205, -235, 0),
        spawn("spawns_single_corner", -85, -245, 90),
        spawn("spawns_training_loop", 0, 265, 180),
    ])

    # 1. Donut Basic.
    donut_center = (-185.0, 150.0)
    for radius in (8, 10, 12):
        objects.append(decal_road(f"donut_ring_{radius}m", _points_circle(*donut_center, radius), looped=True))
    objects.extend(_cross("donut_center", *donut_center))

    # 2. Large Circle.
    circle_center = (65.0, 150.0)
    for radius in (15, 20, 25):
        objects.append(decal_road(f"large_circle_{radius}m", _points_circle(*circle_center, radius), looped=True))
    objects.extend(_cross("large_circle_center", *circle_center))

    # 3/4. Figure eights.
    objects.append(decal_road(
        "figure_eight_easy",
        _points_lemniscate(-155, -85, half_width=42, half_height=30),
        looped=True,
    ))
    objects.extend(_cross("figure_eight_easy_center", -155, -85, arm=1.5))

    objects.append(decal_road(
        "figure_eight_normal",
        _points_lemniscate(45, -85, half_width=32, half_height=22),
        looped=True,
    ))
    objects.extend(_cross("figure_eight_normal_center", 45, -85, arm=1.5))

    # 5. Transition lane. Small ground circles act as "virtual cones".
    gate_y = [-190, -155, -120, -85, -50, -15, 20]
    for idx, y in enumerate(gate_y):
        x = 175 + (15 if idx % 2 else -15)
        objects.append(decal_road(
            f"transition_marker_{idx + 1}",
            _points_circle(x, y, 1.4, count=28, width=0.14),
            looped=True,
        ))
    transition_path = [(160 + 22 * math.sin(i * math.pi / 3), -210 + i * 38) for i in range(7)]
    objects.append(decal_road("transition_lane_guide", _points_polyline(transition_path, width=0.12)))

    # 6. Single corner: approach -> 100 degree constant-radius arc -> exit.
    approach = [(-115, -225), (-75, -225), (-35, -225)]
    objects.append(decal_road("single_corner_approach", _points_polyline(approach, width=0.14)))
    corner_center = (-35, -190)
    objects.append(decal_road("single_corner_inner", _arc(*corner_center, 30, -90, 15, width=0.14)))
    objects.append(decal_road("single_corner_outer", _arc(*corner_center, 38, -90, 15, width=0.14)))
    exit_line = [(2, -182), (35, -173), (70, -164)]
    objects.append(decal_road("single_corner_exit", _points_polyline(exit_line, width=0.14)))

    # 7. Advanced training loop around the exercise field.
    loop = [
        (-250, 245), (-140, 270), (20, 265), (175, 235), (245, 145),
        (250, 10), (230, -135), (145, -245), (0, -275), (-155, -250),
        (-245, -155), (-270, -20), (-265, 120),
    ]
    objects.append(decal_road("training_loop_guide", _points_polyline(loop, width=0.22), looped=True))

    return objects


def build_materials() -> dict:
    return {
        ASPHALT_MATERIAL: {
            "name": ASPHALT_MATERIAL,
            "mapTo": ASPHALT_MATERIAL,
            "class": "Material",
            "Stages": [
                {"baseColorFactor": [0.115, 0.12, 0.125, 1], "roughnessFactor": 0.94, "metallicFactor": 0},
                {}, {}, {}
            ],
            "groundType": "ASPHALT",
            "annotation": "ASPHALT",
            "materialTag0": "beamng",
            "materialTag1": "road",
            "version": 1.5,
        },
        MARKING_MATERIAL: {
            "name": MARKING_MATERIAL,
            "mapTo": MARKING_MATERIAL,
            "class": "Material",
            "Stages": [
                {"baseColorFactor": [0.92, 0.92, 0.88, 1], "roughnessFactor": 0.78, "metallicFactor": 0},
                {}, {}, {}
            ],
            "groundType": "ASPHALT",
            "annotation": "ROAD",
            "materialTag0": "beamng",
            "materialTag1": "road",
            "version": 1.5,
        },
    }


def build_info() -> dict:
    spawn_meta = [
        ("spawns_default", "Default / Staging", "Central staging area and start of the training loop."),
        ("spawns_donut", "Donut Basic", "Concentric 8 m, 10 m and 12 m guide circles."),
        ("spawns_large_circle", "Large Circle", "Concentric 15 m, 20 m and 25 m steady-state drift guides."),
        ("spawns_figure_eight_easy", "Figure Eight - Easy", "Wide figure-eight for slow, deliberate transitions."),
        ("spawns_figure_eight_normal", "Figure Eight - Normal", "Tighter figure-eight requiring cleaner transitions."),
        ("spawns_transition_lane", "Transition Lane", "Repeated alternating markers for left/right transition practice."),
        ("spawns_single_corner", "Single Corner", "Approach, sustained constant-radius corner and marked exit."),
        ("spawns_training_loop", "Training Loop", "Short perimeter loop combining the fundamental skills."),
    ]
    return {
        "title": "Drift Training Pad",
        "description": "A compact structured training facility for learning donuts, steady-state circles, figure-eights, transitions and corner-entry control.",
        "authors": "Alexey (chinn-choppa) and contributors",
        "features": "Structured drift exercises with repeatable guide geometry and dedicated spawn points.",
        "suitablefor": "Drift training and vehicle-control practice",
        "roads": "Flat asphalt training pad",
        "defaultSpawnPointName": "spawns_default",
        "defaultDate": {"year": 2026, "month": 6, "day": 20},
        "size": [600, 600],
        "supportsTraffic": False,
        "supportsTimeOfDay": True,
        "previews": ["preview.png"],
        "spawnPoints": [
            {
                "translationId": label,
                "description": description,
                "objectname": object_name,
                "preview": "preview.png",
            }
            for object_name, label, description in spawn_meta
        ],
    }


def render_ndjson(objects: Iterable[dict]) -> str:
    return "".join(json.dumps(obj, separators=(",", ":"), sort_keys=False) + "\n" for obj in objects)


def expected_outputs(repo_root: Path) -> dict[Path, str]:
    return {
        repo_root / SCENE_ROOT: json.dumps({"name": "MissionGroup", "class": "SimGroup"}, separators=(",", ":")) + "\n",
        repo_root / MISSION_ITEMS: render_ndjson(build_objects()),
        repo_root / MATERIALS: json.dumps(build_materials(), indent=2) + "\n",
        repo_root / INFO: json.dumps(build_info(), indent=2, ensure_ascii=False) + "\n",
    }


def generate(repo_root: Path, *, check: bool = False) -> bool:
    mismatches: list[Path] = []
    for path, expected in expected_outputs(repo_root).items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                mismatches.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
    if mismatches:
        for path in mismatches:
            print(f"generated file is stale or missing: {path.relative_to(repo_root)}")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated level files differ from committed files")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    return 0 if generate(args.repo_root.resolve(), check=args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
