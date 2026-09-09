from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = Path(
    r"C:\Users\25450\Desktop\智能体数据集_黄河滩区边界裁剪结果_最终(6)\智能体数据集_黄河滩区边界裁剪结果_最终"
)
SOURCE_ROOT = Path(os.environ.get("HPU_REAL_DATA_ROOT", DEFAULT_SOURCE_ROOT))
RAW_CLCD_2024 = SOURCE_ROOT / "1.土地利用_CLCD_30m" / "CLCD_2024_黄河滩区中下游裁剪.tif"
TEMPLATE_CLCD_2020 = ROOT / "data" / "processed" / "aligned" / "clcd_2020_epsg4326_250m.tif"
ALIGNED_CLCD_2024 = ROOT / "data" / "processed" / "aligned" / "clcd_2024_epsg4326_250m.tif"
OVERLAY_CLCD_2024 = ROOT / "frontend" / "data" / "overlays" / "clcd_2024.png"
QUERY_GRID_CLCD_2024 = ROOT / "frontend" / "data" / "query_grids" / "clcd_2024.json"
STATS_JS = ROOT / "frontend" / "data" / "config" / "layerStats2024.js"

GRID_WIDTH = 200
GRID_HEIGHT = 99
YEAR = 2024

PALETTE = {
    1: (230, 204, 110),
    2: (38, 110, 62),
    3: (98, 140, 58),
    4: (140, 178, 78),
    5: (32, 118, 168),
    6: (188, 176, 132),
    7: (150, 108, 66),
    8: (196, 72, 42),
    9: (108, 102, 88),
}


def align_to_2020_template() -> Path:
    if not RAW_CLCD_2024.exists():
        raise FileNotFoundError(RAW_CLCD_2024)
    if not TEMPLATE_CLCD_2020.exists():
        raise FileNotFoundError(TEMPLATE_CLCD_2020)

    ALIGNED_CLCD_2024.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(TEMPLATE_CLCD_2020) as template, rasterio.open(RAW_CLCD_2024) as src:
        destination = np.zeros((template.height, template.width), dtype=np.uint8)
        reproject(
            source=rasterio.band(src, 1),
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=template.transform,
            dst_crs=template.crs,
            dst_nodata=0,
            resampling=Resampling.nearest,
        )
        profile = template.profile.copy()
        profile.update(driver="GTiff", dtype="uint8", count=1, nodata=0, compress="deflate", predictor=2)
        with rasterio.open(ALIGNED_CLCD_2024, "w", **profile) as dst:
            dst.write(destination, 1)
    return ALIGNED_CLCD_2024


def build_overlay(path: Path) -> Path:
    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata
    rgba = np.zeros((*arr.shape, 4), dtype=np.uint8)
    for value, color in PALETTE.items():
        mask = arr == value
        rgba[mask, :3] = color
        rgba[mask, 3] = 240
    if nodata is not None:
        rgba[arr == nodata, 3] = 0
    OVERLAY_CLCD_2024.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(OVERLAY_CLCD_2024, compress_level=1)
    return OVERLAY_CLCD_2024


def build_query_grid(path: Path) -> Path:
    with rasterio.open(path) as src:
        data = src.read(1, out_shape=(GRID_HEIGHT, GRID_WIDTH), resampling=Resampling.nearest, masked=True)
        values = data.astype("float32").filled(np.nan)
        if src.nodata is not None:
            values[np.isclose(values, src.nodata)] = np.nan
        payload = {
            "layer": "clcd",
            "year": YEAR,
            "source": str(path),
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "bounds": {
                "west": src.bounds.left,
                "south": src.bounds.bottom,
                "east": src.bounds.right,
                "north": src.bounds.top,
            },
            "values": [[None if np.isnan(v) else int(v) for v in row] for row in values],
        }
    QUERY_GRID_CLCD_2024.parent.mkdir(parents=True, exist_ok=True)
    QUERY_GRID_CLCD_2024.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return QUERY_GRID_CLCD_2024


def compute_stats(path: Path) -> dict:
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        valid = np.isfinite(arr) & (arr != 0)
        values = arr[valid]
        if values.size == 0:
            return {"available": False, "sourceYear": YEAR, "validRatio": 0, "min": None, "median": None, "p90": None, "max": None, "file": str(path)}
        q = np.nanpercentile(values.astype("float64"), [0, 50, 90, 100])
        return {
            "available": True,
            "sourceYear": YEAR,
            "validRatio": round(float(values.size / arr.size), 6),
            "min": round(float(q[0]), 4),
            "median": round(float(q[1]), 4),
            "p90": round(float(q[2]), 4),
            "max": round(float(q[3]), 4),
            "file": str(path),
        }


def update_stats_js(stats: dict) -> None:
    if STATS_JS.exists():
        text = STATS_JS.read_text(encoding="utf-8").strip()
        prefix = "window.LAYER_STATS_2024 = "
        payload = json.loads(text[len(prefix):].rstrip(";")) if text.startswith(prefix) else {str(YEAR): {}}
    else:
        payload = {str(YEAR): {}}
    payload.setdefault(str(YEAR), {})["clcd"] = stats
    STATS_JS.parent.mkdir(parents=True, exist_ok=True)
    STATS_JS.write_text(f"window.LAYER_STATS_2024 = {json.dumps(payload, ensure_ascii=False, indent=2)};\n", encoding="utf-8")


def print_meta(label: str, path: Path) -> None:
    with rasterio.open(path) as src:
        print(f"{label}")
        print(f"  crs={src.crs}")
        print(f"  transform={src.transform}")
        print(f"  bounds={src.bounds}")
        print(f"  width={src.width} height={src.height}")
        print(f"  res={src.res}")
        print(f"  nodata={src.nodata}")


def main() -> None:
    print_meta("raw 2024", RAW_CLCD_2024)
    print_meta("template 2020", TEMPLATE_CLCD_2020)
    aligned = align_to_2020_template()
    overlay = build_overlay(aligned)
    grid = build_query_grid(aligned)
    stats = compute_stats(aligned)
    update_stats_js(stats)
    print_meta("aligned 2024", aligned)
    print(f"wrote {aligned.relative_to(ROOT)}")
    print(f"wrote {overlay.relative_to(ROOT)}")
    print(f"wrote {grid.relative_to(ROOT)}")
    print(f"updated {STATS_JS.relative_to(ROOT)}")
    print(f"stats median={stats['median']} valid={stats['validRatio']}")


if __name__ == "__main__":
    main()
