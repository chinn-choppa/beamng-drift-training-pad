from __future__ import annotations

import argparse
import json
import math
import struct
import zlib
from pathlib import Path

LEVEL_ID = "drift_training_pad"
LEVEL_ROOT = Path("levels") / LEVEL_ID
MISSION_ITEMS = LEVEL_ROOT / "main" / "MissionGroup" / "items.level.json"
MATERIALS = LEVEL_ROOT / "main.materials.json"
GRAPHICS_DAE = LEVEL_ROOT / "art" / "shapes" / "facility_graphics.dae"
BOUNDARIES_DAE = LEVEL_ROOT / "art" / "shapes" / "facility_boundaries.dae"
CONE_DAE = LEVEL_ROOT / "art" / "shapes" / "training_cone.dae"
SCENERY_DAE = LEVEL_ROOT / "art" / "shapes" / "facility_scenery.dae"
ASPHALT_BASE_TEXTURE = LEVEL_ROOT / "art" / "textures" / "asphalt_b.color.png"
ASPHALT_ROUGHNESS_TEXTURE = LEVEL_ROOT / "art" / "textures" / "asphalt_r.data.png"

IDENTITY = [1, 0, 0, 0, 1, 0, 0, 0, 1]
ASPHALT_MATERIAL = "driftpad_asphalt"
GRAPHICS_MATERIAL = "driftpad_training_yellow"
CONCRETE_MATERIAL = "driftpad_concrete"
CONE_MATERIAL = "driftpad_cone_orange"
GRASS_MATERIAL = "driftpad_grass_visual"
GRAPHICS_MESH_NAME = "facility_graphics_mesh"
BOUNDARY_MESH_NAME = "facility_boundaries_mesh"
SCENERY_MESH_NAME = "facility_scenery_mesh"
GRAPHICS_MESH_PATH = f"/{GRAPHICS_DAE.as_posix()}"
BOUNDARY_MESH_PATH = f"/{BOUNDARIES_DAE.as_posix()}"
CONE_MESH_PATH = f"/{CONE_DAE.as_posix()}"
SCENERY_MESH_PATH = f"/{SCENERY_DAE.as_posix()}"
FACILITY_HALF_SIZE = 282.0

ZONE_SPECS = (
    ("donut", "01 DONUT", (-238.0, 92.0, -130.0, 222.0)),
    ("large_circle", "02 CIRCLE", (10.0, 92.0, 120.0, 222.0)),
    ("figure_eight_easy", "03 FIG 8 EASY", (-220.0, -145.0, -92.0, -28.0)),
    ("figure_eight_normal", "04 FIG 8", (-5.0, -137.0, 100.0, -35.0)),
    ("transition_lane", "05 TRANSITION", (118.0, -236.0, 220.0, 42.0)),
    ("single_corner", "06 CORNER", (-138.0, -262.0, 95.0, -145.0)),
    ("training_loop", "07 LOOP", (-270.0, 232.0, -150.0, 272.0)),
)

FONT_5X7 = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
}


def _round(value: float) -> float:
    return round(float(value), 4)


def _tsstatic(name: str, path: str, *, collision: str = "None", position=(0, 0, 0)) -> dict:
    return {
        "name": name,
        "class": "TSStatic",
        "__parent": "MissionGroup",
        "shapeName": path,
        "position": [_round(position[0]), _round(position[1]), _round(position[2])],
        "rotationMatrix": IDENTITY,
        "scale": [1, 1, 1],
        "collisionType": collision,
        "decalType": "None",
        "isRenderEnabled": True,
    }


def _cone_positions() -> list[tuple[str, float, float]]:
    result = [
        ("cone_donut_center", -185, 150),
        ("cone_circle_center", 65, 150),
        ("cone_fig8_easy_left", -183, -85),
        ("cone_fig8_easy_right", -127, -85),
        ("cone_fig8_normal_left", 23, -85),
        ("cone_fig8_normal_right", 67, -85),
        ("cone_corner_apex", -5, -194),
    ]
    for idx, y in enumerate([-190, -155, -120, -85, -50, -15, 20]):
        x = 175 + (15 if idx % 2 else -15)
        result.append((f"cone_transition_{idx + 1}", x, y))
    return result


def _polish_object_names() -> set[str]:
    return {
        GRAPHICS_MESH_NAME,
        BOUNDARY_MESH_NAME,
        SCENERY_MESH_NAME,
        *[name for name, _, _ in _cone_positions()],
    }


def _load_objects(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _canonical_objects(objects: list[dict]) -> list[dict]:
    names = _polish_object_names()
    result = [obj for obj in objects if obj.get("name") not in names]
    grounds = [
        obj for obj in result
        if obj.get("class") == "GroundPlane" and obj.get("name") == "training_ground"
    ]
    if len(grounds) != 1:
        raise ValueError(f"expected exactly one training_ground GroundPlane, found {len(grounds)}")
    grounds[0]["scaleU"] = 24
    grounds[0]["scaleV"] = 24
    result.extend([
        _tsstatic(GRAPHICS_MESH_NAME, GRAPHICS_MESH_PATH, collision="None"),
        _tsstatic(BOUNDARY_MESH_NAME, BOUNDARY_MESH_PATH, collision="Visible Mesh"),
        _tsstatic(SCENERY_MESH_NAME, SCENERY_MESH_PATH, collision="None"),
    ])
    for name, x, y in _cone_positions():
        result.append(_tsstatic(name, CONE_MESH_PATH, collision="None", position=(x, y, 0.04)))
    return result


def _canonical_materials(materials: dict) -> dict:
    result = json.loads(json.dumps(materials))
    if ASPHALT_MATERIAL not in result:
        raise ValueError(f"missing base material {ASPHALT_MATERIAL}")
    asphalt = result[ASPHALT_MATERIAL]
    stages = asphalt.setdefault("Stages", [{}, {}, {}, {}])
    while len(stages) < 4:
        stages.append({})
    stages[0] = {
        "baseColorMap": f"/{ASPHALT_BASE_TEXTURE.as_posix()}",
        "roughnessMap": f"/{ASPHALT_ROUGHNESS_TEXTURE.as_posix()}",
        "baseColorFactor": [0.82, 0.84, 0.88, 1],
        "roughnessFactor": 1,
        "metallicFactor": 0,
    }
    asphalt["activeLayers"] = 1
    asphalt["groundType"] = "ASPHALT"
    asphalt["annotation"] = "ASPHALT"
    asphalt["version"] = 1.5
    result.update({
        GRAPHICS_MATERIAL: {
            "name": GRAPHICS_MATERIAL,
            "mapTo": GRAPHICS_MATERIAL,
            "class": "Material",
            "Stages": [
                {"baseColorFactor": [0.95, 0.60, 0.08, 1], "roughnessFactor": 0.82, "metallicFactor": 0},
                {}, {}, {},
            ],
            "activeLayers": 1,
            "annotation": "ROAD",
            "version": 1.5,
        },
        CONCRETE_MATERIAL: {
            "name": CONCRETE_MATERIAL,
            "mapTo": CONCRETE_MATERIAL,
            "class": "Material",
            "Stages": [
                {"baseColorFactor": [0.26, 0.28, 0.30, 1], "roughnessFactor": 0.96, "metallicFactor": 0},
                {}, {}, {},
            ],
            "activeLayers": 1,
            "annotation": "BUILDING",
            "version": 1.5,
        },
        CONE_MATERIAL: {
            "name": CONE_MATERIAL,
            "mapTo": CONE_MATERIAL,
            "class": "Material",
            "Stages": [
                {"baseColorFactor": [0.96, 0.25, 0.04, 1], "roughnessFactor": 0.72, "metallicFactor": 0},
                {}, {}, {},
            ],
            "activeLayers": 1,
            "annotation": "OBJECT",
            "version": 1.5,
        },
        GRASS_MATERIAL: {
            "name": GRASS_MATERIAL,
            "mapTo": GRASS_MATERIAL,
            "class": "Material",
            "Stages": [
                {"baseColorFactor": [0.14, 0.22, 0.09, 1], "roughnessFactor": 1, "metallicFactor": 0},
                {}, {}, {},
            ],
            "activeLayers": 1,
            "annotation": "NATURE",
            "version": 1.5,
        },
    })
    return result


def _segment_quad(a, b, *, width: float, z: float):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return None
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    return [
        (ax + nx, ay + ny, z),
        (ax - nx, ay - ny, z),
        (bx - nx, by - ny, z),
        (bx + nx, by + ny, z),
    ]


def _add_line(vertices, indices, a, b, width=0.35, z=0.045):
    quad = _segment_quad(a, b, width=width, z=z)
    if quad is None:
        return
    base = len(vertices)
    vertices.extend(quad)
    indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])


def _add_xy_quad(vertices, indices, x0, y0, x1, y1, z=0.05):
    base = len(vertices)
    vertices.extend([(x0, y0, z), (x0, y1, z), (x1, y1, z), (x1, y0, z)])
    indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])


def _add_box(vertices, indices, cx, cy, sx, sy, height, z0=0.0):
    x0, x1 = cx - sx / 2, cx + sx / 2
    y0, y1 = cy - sy / 2, cy + sy / 2
    z1 = z0 + height
    base = len(vertices)
    vertices.extend([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ])
    for a, b, c, d in [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]:
        indices.extend([base + a, base + b, base + c, base + a, base + c, base + d])


def _add_frame_corners(vertices, indices, rect, corner=8.0, width=0.45):
    x0, y0, x1, y1 = rect
    segments = [
        ((x0, y0), (x0 + corner, y0)), ((x0, y0), (x0, y0 + corner)),
        ((x1, y0), (x1 - corner, y0)), ((x1, y0), (x1, y0 + corner)),
        ((x0, y1), (x0 + corner, y1)), ((x0, y1), (x0, y1 - corner)),
        ((x1, y1), (x1 - corner, y1)), ((x1, y1), (x1, y1 - corner)),
    ]
    for a, b in segments:
        _add_line(vertices, indices, a, b, width=width)


def _text_width(text: str, scale: float) -> float:
    return sum((6 if ch != " " else 3) * scale for ch in text)


def _add_text(vertices, indices, text: str, x: float, y: float, scale=0.62, z=0.05):
    cursor = x
    for ch in text:
        if ch == " ":
            cursor += 3 * scale
            continue
        glyph = FONT_5X7.get(ch)
        if glyph is None:
            cursor += 6 * scale
            continue
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    px0 = cursor + col * scale
                    py0 = y - row * scale
                    _add_xy_quad(vertices, indices, px0, py0 - scale, px0 + scale * 0.86, py0, z)
        cursor += 6 * scale


def _dae_single(material: str, geometry_id: str, vertices, indices) -> str:
    positions = " ".join(f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in vertices)
    triangles = " ".join(str(i) for i in indices)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><contributor><authoring_tool>beamng-drift-training-pad deterministic generator</authoring_tool></contributor><unit name="meter" meter="1"/><up_axis>Z_UP</up_axis></asset>
  <library_effects><effect id="{material}-effect"><profile_COMMON><technique sid="common"><lambert><diffuse><color>1 1 1 1</color></diffuse></lambert></technique></profile_COMMON></effect></library_effects>
  <library_materials><material id="{material}-material" name="{material}"><instance_effect url="#{material}-effect"/></material></library_materials>
  <library_geometries><geometry id="{geometry_id}-geometry" name="{geometry_id}"><mesh><source id="{geometry_id}-positions"><float_array id="{geometry_id}-positions-array" count="{len(vertices) * 3}">{positions}</float_array><technique_common><accessor source="#{geometry_id}-positions-array" count="{len(vertices)}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source><vertices id="{geometry_id}-vertices"><input semantic="POSITION" source="#{geometry_id}-positions"/></vertices><triangles material="{material}" count="{len(indices) // 3}"><input semantic="VERTEX" source="#{geometry_id}-vertices" offset="0"/><p>{triangles}</p></triangles></mesh></geometry></library_geometries>
  <library_visual_scenes><visual_scene id="Scene" name="Scene"><node id="{geometry_id}" name="{geometry_id}" type="NODE"><instance_geometry url="#{geometry_id}-geometry"><bind_material><technique_common><instance_material symbol="{material}" target="#{material}-material"/></technique_common></bind_material></instance_geometry></node></visual_scene></library_visual_scenes><scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>\n'''


def build_graphics_dae() -> str:
    vertices, indices = [], []
    h = FACILITY_HALF_SIZE - 3
    for a, b in [
        ((-h, -h), (h, -h)), ((h, -h), (h, h)),
        ((h, h), (-h, h)), ((-h, h), (-h, -h)),
    ]:
        _add_line(vertices, indices, a, b, width=0.75)
    for _, label, rect in ZONE_SPECS:
        _add_frame_corners(vertices, indices, rect)
        x0, _, x1, y1 = rect
        label_w = _text_width(label, 0.62)
        _add_text(vertices, indices, label, min(x0 + 4, x1 - label_w - 4), y1 - 4)
    _add_text(vertices, indices, "START", -18, 265, scale=0.78)
    for x in (-36, -18, 0, 18, 36):
        _add_line(vertices, indices, (x, 238), (x, 258), width=0.22)
    _add_line(vertices, indices, (-36, 238), (36, 238), width=0.22)
    _add_line(vertices, indices, (-36, 258), (36, 258), width=0.22)
    _add_line(vertices, indices, (0, 230), (0, 212), width=0.5)
    _add_line(vertices, indices, (0, 212), (-5, 219), width=0.5)
    _add_line(vertices, indices, (0, 212), (5, 219), width=0.5)
    return _dae_single(GRAPHICS_MATERIAL, "facility_graphics", vertices, indices)


def build_boundaries_dae() -> str:
    vertices, indices = [], []
    h, wall_h, wall_t = FACILITY_HALF_SIZE, 0.72, 0.65
    _add_box(vertices, indices, 0, h, 2 * h, wall_t, wall_h)
    _add_box(vertices, indices, 0, -h, 2 * h, wall_t, wall_h)
    _add_box(vertices, indices, h, 0, wall_t, 2 * h, wall_h)
    _add_box(vertices, indices, -h, 0, wall_t, 2 * h, wall_h)
    return _dae_single(CONCRETE_MATERIAL, "facility_boundaries", vertices, indices)


def build_scenery_dae() -> str:
    vertices, indices = [], []
    h, outer, z = FACILITY_HALF_SIZE + 1, 420.0, 0.012
    _add_xy_quad(vertices, indices, -outer, h, outer, outer, z)
    _add_xy_quad(vertices, indices, -outer, -outer, outer, -h, z)
    _add_xy_quad(vertices, indices, -outer, -h, -h, h, z)
    _add_xy_quad(vertices, indices, h, -h, outer, h, z)
    return _dae_single(GRASS_MATERIAL, "facility_scenery", vertices, indices)


def build_cone_dae() -> str:
    vertices, indices = [], []
    sides, r0, r1, height = 12, 0.28, 0.055, 0.58
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((r0 * math.cos(a), r0 * math.sin(a), 0.02))
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((r1 * math.cos(a), r1 * math.sin(a), height))
    for i in range(sides):
        j = (i + 1) % sides
        indices.extend([i, j, sides + j, i, sides + j, sides + i])
    base_center = len(vertices)
    vertices.append((0, 0, 0.02))
    top_center = len(vertices)
    vertices.append((0, 0, height))
    for i in range(sides):
        j = (i + 1) % sides
        indices.extend([base_center, j, i, top_center, sides + i, sides + j])
    return _dae_single(CONE_MATERIAL, "training_cone", vertices, indices)


def _png_rgb(width: int, height: int, rgb: bytes) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind, data):
        return (
            struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    rows = bytearray()
    stride = width * 3
    for y in range(height):
        rows.append(0)
        rows.extend(rgb[y * stride:(y + 1) * stride])
    return (
        signature
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + chunk(b"IEND", b"")
    )


def _asphalt_value(x: int, y: int, size: int) -> float:
    value = 0.0
    for k, amplitude in ((1, 5.0), (2, 3.0), (5, 1.8), (11, 1.2), (23, 0.7)):
        value += (
            amplitude
            * math.sin(2 * math.pi * k * x / size + 0.37 * k)
            * math.cos(2 * math.pi * (k + 1) * y / size + 0.19 * k)
        )
    value += ((((x * 73856093) ^ (y * 19349663)) & 31) - 15) * 0.12
    return value


def build_asphalt_base_png(size: int = 256) -> bytes:
    buf = bytearray()
    for y in range(size):
        for x in range(size):
            noise = _asphalt_value(x, y, size)
            base = max(42, min(88, int(64 + noise)))
            warm = 1 if ((x * 17 + y * 29) % 97) == 0 else 0
            buf.extend((base + warm, base + warm, min(92, base + 2)))
    return _png_rgb(size, size, bytes(buf))


def build_asphalt_roughness_png(size: int = 256) -> bytes:
    buf = bytearray()
    for y in range(size):
        for x in range(size):
            value = max(205, min(250, int(231 + _asphalt_value(x, y, size) * 0.8)))
            buf.extend((value, value, value))
    return _png_rgb(size, size, bytes(buf))


def _expected(repo_root: Path):
    objects = _canonical_objects(_load_objects(repo_root / MISSION_ITEMS))
    materials = _canonical_materials(json.loads((repo_root / MATERIALS).read_text(encoding="utf-8")))
    text = {
        repo_root / MISSION_ITEMS: "".join(
            json.dumps(obj, separators=(",", ":"), sort_keys=False) + "\n" for obj in objects
        ),
        repo_root / MATERIALS: json.dumps(materials, indent=2) + "\n",
        repo_root / GRAPHICS_DAE: build_graphics_dae(),
        repo_root / BOUNDARIES_DAE: build_boundaries_dae(),
        repo_root / CONE_DAE: build_cone_dae(),
        repo_root / SCENERY_DAE: build_scenery_dae(),
    }
    binary = {
        repo_root / ASPHALT_BASE_TEXTURE: build_asphalt_base_png(),
        repo_root / ASPHALT_ROUGHNESS_TEXTURE: build_asphalt_roughness_png(),
    }
    return text, binary


def apply(repo_root: Path, *, check: bool = False) -> bool:
    text, binary = _expected(repo_root)
    mismatches = []
    for path, expected in text.items():
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                mismatches.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
    for path, expected in binary.items():
        if check:
            if not path.is_file() or path.read_bytes() != expected:
                mismatches.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        for path in mismatches:
            print(f"visual-polish file is stale or missing: {path.relative_to(repo_root)}")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply deterministic visual/readability assets to the generated BeamNG level."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        ok = apply(args.repo_root.resolve(), check=args.check)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
