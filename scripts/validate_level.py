from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

LEVEL_ID = "drift_training_pad"
LEVEL_ROOT = Path("levels") / LEVEL_ID
MARKINGS_REL = Path("art") / "shapes" / "training_markings.dae"
MARKINGS_PATH = f"/{(LEVEL_ROOT / MARKINGS_REL).as_posix()}"
MARKING_MESH_NAME = "training_markings_mesh"
MARKING_MATERIAL = "driftpad_marking_white"
FORBIDDEN_PARTS = {"source", "build", "dist", "__pycache__", ".git"}
ABSOLUTE_WINDOWS_PATH = re.compile(r"[A-Za-z]:[\\/]")


class ValidationError(Exception):
    pass


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc


def _load_ndjson(path: Path) -> list[dict]:
    objects: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValidationError(f"{path}: cannot read: {exc}") from exc

    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{lineno}: invalid NDJSON object: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValidationError(f"{path}:{lineno}: each line must be a JSON object")
        if not isinstance(obj.get("class"), str) or not obj["class"]:
            raise ValidationError(f"{path}:{lineno}: missing non-empty class")
        objects.append(obj)
    if not objects:
        raise ValidationError(f"{path}: file contains no objects")
    return objects


def _validate_markings_dae(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing generated visual markings mesh: {path}"]
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [f"{path}: invalid COLLADA XML: {exc}"]
    namespace = "{http://www.collada.org/2005/11/COLLADASchema}"
    if root.tag != namespace + "COLLADA":
        errors.append(f"{path}: root must be COLLADA 1.4.1")
        return errors
    triangles = root.findall(f".//{namespace}triangles")
    triangle_count = 0
    for tri in triangles:
        try:
            triangle_count += int(tri.get("count", "0"))
        except ValueError:
            errors.append(f"{path}: triangles count is not an integer")
    if triangle_count <= 0:
        errors.append(f"{path}: visual markings mesh contains no triangles")
    material_names = {node.get("name") for node in root.findall(f".//{namespace}material")}
    if MARKING_MATERIAL not in material_names:
        errors.append(f"{path}: missing COLLADA material {MARKING_MATERIAL!r}")
    return errors


def validate(repo_root: Path) -> list[str]:
    errors: list[str] = []
    level_root = repo_root / LEVEL_ROOT
    info_path = level_root / "info.json"
    materials_path = level_root / "main.materials.json"
    scene_root = level_root / "main" / "items.level.json"
    markings_path = level_root / MARKINGS_REL

    for path in (info_path, materials_path, scene_root, markings_path):
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(repo_root)}")
    if errors:
        return errors

    try:
        info = _load_json(info_path)
        materials = _load_json(materials_path)
    except ValidationError as exc:
        return [str(exc)]

    if not isinstance(info, dict):
        errors.append("info.json must contain an object")
        info = {}
    if not isinstance(materials, dict):
        errors.append("main.materials.json must contain an object")
        materials = {}

    ndjson_paths = sorted(level_root.rglob("items.level.json"))
    all_objects: list[dict] = []
    for path in ndjson_paths:
        try:
            all_objects.extend(_load_ndjson(path))
        except ValidationError as exc:
            errors.append(str(exc))

    if not all_objects:
        errors.append("no level objects were loaded")
        return errors

    names: dict[str, str] = {}
    for obj in all_objects:
        name = obj.get("name")
        if isinstance(name, str) and name:
            if name in names:
                errors.append(f"duplicate object name: {name}")
            names[name] = obj.get("class", "")

    mission_groups = [o for o in all_objects if o.get("class") == "SimGroup" and o.get("name") == "MissionGroup"]
    if len(mission_groups) != 1:
        errors.append(f"expected exactly one MissionGroup SimGroup, found {len(mission_groups)}")

    level_infos = [o for o in all_objects if o.get("class") == "LevelInfo" and o.get("name") == "theLevelInfo"]
    if len(level_infos) != 1:
        errors.append(f"expected exactly one theLevelInfo, found {len(level_infos)}")
    elif level_infos[0].get("globalEnviromentMap") != "DefaultSkyCubemap":
        errors.append("theLevelInfo must define globalEnviromentMap=DefaultSkyCubemap")

    cloud_layers = [o for o in all_objects if o.get("class") == "CloudLayer"]
    if cloud_layers:
        errors.append("MVP must not include CloudLayer without an explicit texture")

    spawns = {o.get("name") for o in all_objects if o.get("class") == "SpawnSphere" and isinstance(o.get("name"), str)}
    default_spawn = info.get("defaultSpawnPointName")
    if default_spawn not in spawns:
        errors.append(f"defaultSpawnPointName does not resolve to SpawnSphere: {default_spawn!r}")

    spawn_meta = info.get("spawnPoints")
    if not isinstance(spawn_meta, list) or not spawn_meta:
        errors.append("info.json must expose at least one spawn point")
        spawn_meta = []

    referenced_spawn_names: set[str] = set()
    for idx, entry in enumerate(spawn_meta):
        if not isinstance(entry, dict):
            errors.append(f"spawnPoints[{idx}] must be an object")
            continue
        object_name = entry.get("objectname")
        if not isinstance(object_name, str) or object_name not in spawns:
            errors.append(f"spawnPoints[{idx}].objectname does not resolve: {object_name!r}")
        else:
            referenced_spawn_names.add(object_name)

    if default_spawn and default_spawn not in referenced_spawn_names:
        errors.append("default spawn must also be listed in info.json spawnPoints")

    ground_planes = [o for o in all_objects if o.get("class") == "GroundPlane"]
    if len(ground_planes) != 1:
        errors.append(f"expected exactly one GroundPlane, found {len(ground_planes)}")
    decal_roads = [o for o in all_objects if o.get("class") == "DecalRoad"]
    if len(decal_roads) < 20:
        errors.append(f"expected at least 20 DecalRoad guide objects, found {len(decal_roads)}")

    marking_meshes = [o for o in all_objects if o.get("class") == "TSStatic" and o.get("name") == MARKING_MESH_NAME]
    if len(marking_meshes) != 1:
        errors.append(f"expected exactly one {MARKING_MESH_NAME} TSStatic, found {len(marking_meshes)}")
    else:
        mesh = marking_meshes[0]
        if mesh.get("shapeName") != MARKINGS_PATH:
            errors.append(f"{MARKING_MESH_NAME}: unexpected shapeName {mesh.get('shapeName')!r}")
        if mesh.get("collisionType") != "None":
            errors.append(f"{MARKING_MESH_NAME}: collisionType must be None")
        if mesh.get("decalType") != "None":
            errors.append(f"{MARKING_MESH_NAME}: decalType must be None")
        if mesh.get("isRenderEnabled") is not True:
            errors.append(f"{MARKING_MESH_NAME}: isRenderEnabled must be true")
    errors.extend(_validate_markings_dae(markings_path))

    referenced_materials: set[str] = set()
    for obj in ground_planes + decal_roads:
        material = obj.get("material")
        if not isinstance(material, str) or not material:
            errors.append(f"{obj.get('name', obj.get('class'))}: missing material")
            continue
        referenced_materials.add(material)
        if material not in materials:
            errors.append(f"{obj.get('name', obj.get('class'))}: unresolved material {material!r}")

    for material_name in referenced_materials:
        definition = materials.get(material_name)
        if not isinstance(definition, dict):
            continue
        if definition.get("class") != "Material":
            errors.append(f"{material_name}: material class must be Material")
        if definition.get("name") != material_name:
            errors.append(f"{material_name}: top-level key and name must match")
        if definition.get("groundType") != "ASPHALT":
            errors.append(f"{material_name}: training surface/guide material must use ASPHALT groundType")
        if definition.get("activeLayers") != 1:
            errors.append(f"{material_name}: activeLayers must be 1 for the authored PBR stage")

    asphalt = materials.get("driftpad_asphalt", {})
    if isinstance(asphalt, dict) and asphalt.get("groundType") != "ASPHALT":
        errors.append("driftpad_asphalt must preserve ordinary ASPHALT ground type")

    previews = info.get("previews", [])
    if not isinstance(previews, list):
        errors.append("info.json previews must be a list")
        previews = []
    for preview in previews:
        if not isinstance(preview, str) or not (level_root / preview).is_file():
            errors.append(f"missing level preview: {preview!r}")
    for entry in spawn_meta:
        if isinstance(entry, dict) and isinstance(entry.get("preview"), str):
            if not (level_root / entry["preview"]).is_file():
                errors.append(f"missing spawn preview: {entry['preview']!r}")

    for path in level_root.rglob("*"):
        rel = path.relative_to(level_root)
        if any(part.lower() in FORBIDDEN_PARTS for part in rel.parts):
            errors.append(f"forbidden authoring/build path under distributable level: {rel}")
        if path.is_file() and path.suffix.lower() in {".bak", ".autosave"}:
            errors.append(f"forbidden editor backup file: {rel}")

    # Only scan JSON/NDJSON for author-local paths. COLLADA contains URI/XML
    # namespaces such as http://..., which intentionally resemble drive paths
    # to a simplistic regex.
    for path in [info_path, materials_path, *ndjson_paths]:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if ABSOLUTE_WINDOWS_PATH.search(text):
            errors.append(f"absolute Windows path found in {path.relative_to(repo_root)}")

    required_names = {
        "donut_ring_8m", "donut_ring_10m", "donut_ring_12m",
        "large_circle_15m", "large_circle_20m", "large_circle_25m",
        "figure_eight_easy", "figure_eight_normal", "transition_lane_guide",
        "single_corner_approach", "single_corner_inner", "single_corner_outer",
        "single_corner_exit", "training_loop_guide", MARKING_MESH_NAME,
    }
    missing_names = sorted(required_names - set(names))
    if missing_names:
        errors.append("missing required training objects: " + ", ".join(missing_names))

    expected_spawns = {
        "spawns_default", "spawns_donut", "spawns_large_circle",
        "spawns_figure_eight_easy", "spawns_figure_eight_normal",
        "spawns_transition_lane", "spawns_single_corner", "spawns_training_loop",
    }
    missing_spawns = sorted(expected_spawns - spawns)
    if missing_spawns:
        errors.append("missing required exercise spawns: " + ", ".join(missing_spawns))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Drift Training Pad distributable level files.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Drift Training Pad static validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
