from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

from validate_level import LEVEL_ID, LEVEL_ROOT, validate

FIXED_ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def package(repo_root: Path, output: Path) -> Path:
    errors = validate(repo_root)
    if errors:
        raise RuntimeError("static validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    level_root = repo_root / LEVEL_ROOT
    files = sorted(path for path in level_root.rglob("*") if path.is_file())
    if not files:
        raise RuntimeError("no distributable level files found")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            arcname = path.relative_to(repo_root).as_posix()
            info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic BeamNG mod ZIP.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("dist") / f"{LEVEL_ID}.zip")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output
    if not output.is_absolute():
        output = repo_root / output
    try:
        path = package(repo_root, output)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Built {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
