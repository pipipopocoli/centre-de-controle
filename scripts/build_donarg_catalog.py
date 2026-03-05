#!/usr/bin/env python3
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

TILE = 16
ALPHA_THRESHOLD = 16


def fixed_entries():
    return [
        {"atlas": "office16", "id": "desk", "label": "Desk", "category": "desks", "footprintW": 2, "footprintH": 2, "isDesk": True, "rect": {"col": 0, "row": 0, "widthTiles": 2, "heightTiles": 2}},
        {"atlas": "office16", "id": "chair", "label": "Chair", "category": "chairs", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 5, "row": 13, "widthTiles": 1, "heightTiles": 1}},
        {"atlas": "office16", "id": "bookshelf", "label": "Bookshelf", "category": "storage", "footprintW": 1, "footprintH": 2, "isDesk": False, "rect": {"col": 10, "row": 5, "widthTiles": 1, "heightTiles": 2}},
        {"atlas": "office16", "id": "plant", "label": "Plant", "category": "decor", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 3, "row": 27, "widthTiles": 1, "heightTiles": 2}},
        {"atlas": "office16", "id": "cooler", "label": "Cooler", "category": "misc", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 8, "row": 14, "widthTiles": 1, "heightTiles": 2}},
        {"atlas": "office16", "id": "whiteboard", "label": "Whiteboard", "category": "decor", "footprintW": 2, "footprintH": 1, "isDesk": False, "rect": {"col": 0, "row": 26, "widthTiles": 2, "heightTiles": 1}},
        {"atlas": "office16", "id": "pc", "label": "PC", "category": "electronics", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 10, "row": 19, "widthTiles": 1, "heightTiles": 1}},
        {"atlas": "office16", "id": "lamp", "label": "Lamp", "category": "decor", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 8, "row": 18, "widthTiles": 1, "heightTiles": 1}},
        {"atlas": "office16", "id": "desk-modern-gray", "label": "Desk Gray", "category": "desks", "footprintW": 2, "footprintH": 2, "isDesk": True, "rect": {"col": 0, "row": 2, "widthTiles": 2, "heightTiles": 2}},
        {"atlas": "office16", "id": "desk-modern-light", "label": "Desk Light", "category": "desks", "footprintW": 2, "footprintH": 2, "isDesk": True, "rect": {"col": 2, "row": 2, "widthTiles": 2, "heightTiles": 2}},
        {"atlas": "office16", "id": "desk-long-wood", "label": "Desk Long", "category": "desks", "footprintW": 3, "footprintH": 2, "isDesk": True, "rect": {"col": 5, "row": 0, "widthTiles": 3, "heightTiles": 2}},
        {"atlas": "office16", "id": "desk-long-white", "label": "Desk White", "category": "desks", "footprintW": 3, "footprintH": 2, "isDesk": True, "rect": {"col": 8, "row": 0, "widthTiles": 3, "heightTiles": 2}},
        {"atlas": "office16", "id": "table-meeting", "label": "Meeting Table", "category": "desks", "footprintW": 4, "footprintH": 2, "isDesk": True, "rect": {"col": 0, "row": 7, "widthTiles": 4, "heightTiles": 2}},
        {"atlas": "office16", "id": "sofa-gray", "label": "Sofa Gray", "category": "misc", "footprintW": 3, "footprintH": 2, "isDesk": False, "rect": {"col": 7, "row": 3, "widthTiles": 3, "heightTiles": 2}},
        {"atlas": "office16", "id": "bookshelf-wood", "label": "Shelf Wood", "category": "storage", "footprintW": 1, "footprintH": 2, "isDesk": False, "rect": {"col": 8, "row": 5, "widthTiles": 1, "heightTiles": 2}},
        {"atlas": "office16", "id": "bookshelf-wide", "label": "Shelf Wide", "category": "storage", "footprintW": 2, "footprintH": 2, "isDesk": False, "rect": {"col": 11, "row": 5, "widthTiles": 2, "heightTiles": 2}},
        {"atlas": "office16", "id": "cabinet-double", "label": "Cabinet", "category": "storage", "footprintW": 2, "footprintH": 2, "isDesk": False, "rect": {"col": 9, "row": 14, "widthTiles": 2, "heightTiles": 2}},
        {"atlas": "office16", "id": "locker", "label": "Locker", "category": "storage", "footprintW": 1, "footprintH": 2, "isDesk": False, "rect": {"col": 11, "row": 14, "widthTiles": 1, "heightTiles": 2}},
        {"atlas": "office16", "id": "vending-machine", "label": "Vending", "category": "electronics", "footprintW": 1, "footprintH": 2, "isDesk": False, "rect": {"col": 13, "row": 14, "widthTiles": 1, "heightTiles": 2}},
        {"atlas": "office16", "id": "clock", "label": "Clock", "category": "decor", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 0, "row": 22, "widthTiles": 1, "heightTiles": 1}},
        {"atlas": "office16", "id": "frame-landscape", "label": "Frame", "category": "decor", "footprintW": 2, "footprintH": 1, "isDesk": False, "rect": {"col": 0, "row": 24, "widthTiles": 2, "heightTiles": 1}},
        {"atlas": "office16", "id": "frame-portrait", "label": "Portrait", "category": "decor", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 3, "row": 24, "widthTiles": 1, "heightTiles": 1}},
        {"atlas": "office16", "id": "plant-tall", "label": "Plant Tall", "category": "decor", "footprintW": 1, "footprintH": 1, "isDesk": False, "rect": {"col": 5, "row": 27, "widthTiles": 1, "heightTiles": 2}},
    ]


def extract_components(atlas_name: str, image_path: Path):
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    pixels = image.load()
    visited = [[False] * width for _ in range(height)]

    def rgba_alpha(x, y):
        return pixels[x, y][3]

    components = []
    for y in range(height):
        for x in range(width):
            if visited[y][x] or rgba_alpha(x, y) < ALPHA_THRESHOLD:
                continue

            queue = deque([(x, y)])
            visited[y][x] = True
            min_x = max_x = x
            min_y = max_y = y
            pixel_count = 0

            while queue:
                cx, cy = queue.popleft()
                pixel_count += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)

                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    if visited[ny][nx] or rgba_alpha(nx, ny) < ALPHA_THRESHOLD:
                        continue
                    visited[ny][nx] = True
                    queue.append((nx, ny))

            col = min_x // TILE
            row = min_y // TILE
            width_tiles = (max_x // TILE) - col + 1
            height_tiles = (max_y // TILE) - row + 1
            area_tiles = width_tiles * height_tiles

            if pixel_count < 80:
                continue
            if width_tiles > 6 or height_tiles > 6:
                continue
            if area_tiles > 24:
                continue

            if width_tiles >= 3 and height_tiles >= 2:
                category = "desks"
                is_desk = True
            elif height_tiles >= 3:
                category = "storage"
                is_desk = False
            elif width_tiles >= 3:
                category = "electronics"
                is_desk = False
            elif width_tiles <= 2 and height_tiles <= 2:
                category = "decor"
                is_desk = False
            else:
                category = "misc"
                is_desk = False

            footprint_w = max(1, min(width_tiles, 3))
            footprint_h = max(1, min(height_tiles, 3))

            components.append(
                {
                    "atlas": atlas_name,
                    "id": "",
                    "label": "",
                    "category": category,
                    "footprintW": footprint_w,
                    "footprintH": footprint_h,
                    "isDesk": is_desk,
                    "rect": {
                        "col": int(col),
                        "row": int(row),
                        "widthTiles": int(width_tiles),
                        "heightTiles": int(height_tiles),
                    },
                }
            )

    components.sort(key=lambda e: (e["rect"]["row"], e["rect"]["col"]))
    for index, entry in enumerate(components, start=1):
        entry["id"] = f"auto-{atlas_name}-{index:03d}"
        entry["label"] = f"Auto {atlas_name.upper()} {index:03d}"
    return components


def main():
    root = Path(__file__).resolve().parents[1]
    donarg_dir = root / "apps" / "cockpit-next-desktop" / "public" / "local-assets" / "donarg"
    out_path = donarg_dir / "furniture-catalog.json"

    office1 = donarg_dir / "B-C-D-E Office 1 No Shadows.png"
    office2 = donarg_dir / "B-C-D-E Office 2 No Shadows.png"

    if not office1.exists() or not office2.exists():
        raise SystemExit("missing Donarg atlases, run import_office_tileset.sh first")

    entries = []
    entries.extend(fixed_entries())
    entries.extend(extract_components("office1", office1))
    entries.extend(extract_components("office2", office2))

    payload = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }

    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[donarg-catalog] wrote {len(entries)} entries to {out_path}")


if __name__ == "__main__":
    main()
