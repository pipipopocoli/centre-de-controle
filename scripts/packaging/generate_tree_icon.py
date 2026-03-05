#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def _png_chunk(tag: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


class Canvas:
    def __init__(self, size: int) -> None:
        self.size = size
        self.data = bytearray(size * size * 4)

    def _idx(self, x: int, y: int) -> int:
        return (y * self.size + x) * 4

    def blend_pixel(self, x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if x < 0 or y < 0 or x >= self.size or y >= self.size:
            return
        src_r, src_g, src_b, src_a = color
        if src_a <= 0:
            return
        i = self._idx(x, y)
        dst_r = self.data[i]
        dst_g = self.data[i + 1]
        dst_b = self.data[i + 2]
        dst_a = self.data[i + 3]
        sa = src_a / 255.0
        da = dst_a / 255.0
        out_a = sa + da * (1.0 - sa)
        if out_a <= 0:
            self.data[i] = 0
            self.data[i + 1] = 0
            self.data[i + 2] = 0
            self.data[i + 3] = 0
            return
        out_r = (src_r * sa + dst_r * da * (1.0 - sa)) / out_a
        out_g = (src_g * sa + dst_g * da * (1.0 - sa)) / out_a
        out_b = (src_b * sa + dst_b * da * (1.0 - sa)) / out_a
        self.data[i] = int(max(min(out_r, 255), 0))
        self.data[i + 1] = int(max(min(out_g, 255), 0))
        self.data[i + 2] = int(max(min(out_b, 255), 0))
        self.data[i + 3] = int(max(min(out_a * 255.0, 255), 0))

    def fill_circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int, int]) -> None:
        r2 = radius * radius
        x0 = max(cx - radius, 0)
        x1 = min(cx + radius, self.size - 1)
        y0 = max(cy - radius, 0)
        y1 = min(cy + radius, self.size - 1)
        for y in range(y0, y1 + 1):
            dy = y - cy
            for x in range(x0, x1 + 1):
                dx = x - cx
                if dx * dx + dy * dy <= r2:
                    self.blend_pixel(x, y, color)

    def fill_rect(self, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, self.size - 1)
        y1 = min(y1, self.size - 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.blend_pixel(x, y, color)

    def write_png(self, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        signature = b"\x89PNG\r\n\x1a\n"
        ihdr = struct.pack(">IIBBBBB", self.size, self.size, 8, 6, 0, 0, 0)
        raw = bytearray()
        stride = self.size * 4
        for y in range(self.size):
            raw.append(0)
            start = y * stride
            raw.extend(self.data[start : start + stride])
        idat = zlib.compress(bytes(raw), 9)
        content = (
            signature
            + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", idat)
            + _png_chunk(b"IEND", b"")
        )
        out_path.write_bytes(content)


def generate_tree_icon(out_path: Path, size: int = 1024) -> None:
    canvas = Canvas(size=size)
    cx = size // 2
    canopy_y = int(size * 0.36)
    base_y = int(size * 0.78)

    # Soft ground shadow.
    canvas.fill_circle(cx, int(size * 0.82), int(size * 0.22), (20, 60, 28, 22))

    # Canopy layers.
    canvas.fill_circle(cx, canopy_y - int(size * 0.10), int(size * 0.20), (60, 170, 88, 255))
    canvas.fill_circle(cx - int(size * 0.14), canopy_y, int(size * 0.18), (49, 150, 75, 255))
    canvas.fill_circle(cx + int(size * 0.14), canopy_y, int(size * 0.18), (49, 150, 75, 255))
    canvas.fill_circle(cx, canopy_y + int(size * 0.10), int(size * 0.19), (40, 132, 66, 255))
    canvas.fill_circle(cx - int(size * 0.08), canopy_y - int(size * 0.06), int(size * 0.07), (109, 215, 121, 175))

    # Trunk.
    trunk_w = int(size * 0.14)
    trunk_h = int(size * 0.35)
    trunk_x0 = cx - trunk_w // 2
    trunk_y0 = base_y - trunk_h
    canvas.fill_rect(trunk_x0, trunk_y0, trunk_x0 + trunk_w, base_y, (121, 78, 44, 255))
    canvas.fill_rect(trunk_x0 + int(size * 0.02), trunk_y0 + int(size * 0.03), trunk_x0 + int(size * 0.04), base_y, (165, 112, 64, 150))

    # Roots.
    canvas.fill_circle(cx - int(size * 0.06), base_y + int(size * 0.01), int(size * 0.05), (107, 70, 39, 235))
    canvas.fill_circle(cx + int(size * 0.06), base_y + int(size * 0.01), int(size * 0.05), (107, 70, 39, 235))

    # Light contour for dock visibility.
    canvas.fill_circle(cx, canopy_y, int(size * 0.24), (255, 255, 255, 20))

    canvas.write_png(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic local tree icon PNG.")
    parser.add_argument(
        "--out",
        default=str(ROOT_DIR / "assets" / "tree-icon.png"),
        help="Output PNG path",
    )
    parser.add_argument("--size", type=int, default=1024, help="Square icon size in px")
    args = parser.parse_args()

    out_path = Path(args.out).expanduser()
    size = max(int(args.size), 256)
    generate_tree_icon(out_path=out_path, size=size)
    print(f"Wrote tree icon: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
