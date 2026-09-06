from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

import generate_level

WIDTH = 1280
HEIGHT = 720
OUTPUT = generate_level.LEVEL_ROOT / "preview.png"

BG = (27, 30, 32)
WHITE = (232, 232, 225)
MUTED = (105, 112, 116)
ORANGE = (239, 148, 40)


def _map_point(x: float, y: float) -> tuple[int, int]:
    left, top, right, bottom = 70, 55, 1210, 675
    px = left + (x + 300) / 600 * (right - left)
    py = bottom - (y + 300) / 600 * (bottom - top)
    return int(round(px)), int(round(py))


def _set_pixel(buf: bytearray, x: int, y: int, color: tuple[int, int, int], radius: int = 0) -> None:
    for yy in range(max(0, y - radius), min(HEIGHT, y + radius + 1)):
        for xx in range(max(0, x - radius), min(WIDTH, x + radius + 1)):
            idx = (yy * WIDTH + xx) * 3
            buf[idx:idx + 3] = bytes(color)


def _line(buf: bytearray, a: tuple[int, int], b: tuple[int, int], color: tuple[int, int, int], thickness: int = 1) -> None:
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _set_pixel(buf, x0, y0, color, max(0, thickness - 1))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _draw_polyline(buf: bytearray, points: list[tuple[int, int]], color: tuple[int, int, int], thickness: int, looped: bool) -> None:
    for a, b in zip(points, points[1:]):
        _line(buf, a, b, color, thickness)
    if looped and len(points) > 2:
        _line(buf, points[-1], points[0], color, thickness)


def _png_bytes(rgb: bytes) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    rows = bytearray()
    stride = WIDTH * 3
    for y in range(HEIGHT):
        rows.append(0)
        start = y * stride
        rows.extend(rgb[start:start + stride])

    return (
        signature
        + chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + chunk(b"IEND", b"")
    )


def render() -> bytes:
    buf = bytearray(BG * (WIDTH * HEIGHT))

    _line(buf, (18, 18), (WIDTH - 19, 18), MUTED, 2)
    _line(buf, (WIDTH - 19, 18), (WIDTH - 19, HEIGHT - 19), MUTED, 2)
    _line(buf, (WIDTH - 19, HEIGHT - 19), (18, HEIGHT - 19), MUTED, 2)
    _line(buf, (18, HEIGHT - 19), (18, 18), MUTED, 2)

    for obj in generate_level.build_objects():
        if obj.get("class") == "DecalRoad":
            points = [_map_point(node[0], node[1]) for node in obj["nodes"]]
            color = MUTED if obj["name"] == "training_loop_guide" else WHITE
            thickness = 1 if obj["name"] == "training_loop_guide" else 2
            _draw_polyline(buf, points, color, thickness, bool(obj.get("looped")))
        elif obj.get("class") == "SpawnSphere":
            x, y = _map_point(obj["position"][0], obj["position"][1])
            _set_pixel(buf, x, y, ORANGE, 4)

    return _png_bytes(bytes(buf))


def generate(repo_root: Path, *, check: bool = False) -> bool:
    path = repo_root / OUTPUT
    expected = render()
    if check:
        return path.is_file() and path.read_bytes() == expected
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(expected)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic schematic level preview.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    ok = generate(args.repo_root.resolve(), check=args.check)
    if not ok:
        print("generated preview is stale or missing")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
