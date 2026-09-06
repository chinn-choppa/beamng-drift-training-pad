from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LEVEL_ID = "drift_training_pad"
LEVEL_ROOT = Path("levels") / LEVEL_ID
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


def validate(repo_root: Path) -> list[str]:
    errors: list[str] = []
    level_root = repo_root / LEVEL_ROOT
    info_path = level_root / "info.json"
    materials_path = level_root / "main.materials.json"
    scene_root = level_root / "main" / "items.level.json"

    for path in (info_path, materials_path, scene_root):
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
        "single_corner_exit", "training_loop_guide",
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
