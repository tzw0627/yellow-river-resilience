from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = Path(
    r"C:\Users\25450\Desktop\智能体数据集_黄河滩区边界裁剪结果_最终(6)\智能体数据集_黄河滩区边界裁剪结果_最终"
)
SOURCE_ROOT = Path(os.environ.get("HPU_REAL_DATA_ROOT", DEFAULT_SOURCE_ROOT))
OVERLAY_DIR = ROOT / "frontend" / "data" / "overlays"
QUERY_GRID_DIR = ROOT / "frontend" / "data" / "query_grids"
CONFIG_DIR = ROOT / "frontend" / "data" / "config"

YEAR = 2024
GRID_WIDTH = 200
GRID_HEIGHT = 99
NODATA_SENTINELS = [-9999, -9999.0, -2147483647, -2147483647.0, -3.4028234663852886e38, -3.4028230607370965e38]

LAYERS = {
    "ndvi": {"path": SOURCE_ROOT / "5.NDVI_250m" / "MODIS_NDVI_AnnualMean_2024.tif", "kind": "continuous", "colors": ((218, 222, 170), (87, 130, 51)), "resampling": Resampling.average},
    "evi": {"path": SOURCE_ROOT / "6.EVI_250m" / "MODIS_EVI_AnnualMean_2024.tif", "kind": "continuous", "colors": ((214, 221, 169), (36, 132, 91)), "resampling": Resampling.average},
    "clcd": {"path": SOURCE_ROOT / "1.土地利用_CLCD_30m" / "CLCD_2024_黄河滩区中下游裁剪.tif", "kind": "clcd", "resampling": Resampling.nearest},
    "water": {"path": SOURCE_ROOT / "7.水体_30m" / "JRC_waterClass_target_2024_data_2021.tif", "kind": "water", "resampling": Resampling.nearest},
    "gdp": {"path": SOURCE_ROOT / "4.GDP_1km" / "GDP_2024_黄河滩区中下游边界.tif", "kind": "continuous", "colors": ((89, 69, 46), (214, 145, 75)), "resampling": Resampling.average},
    "ntl": {"path": SOURCE_ROOT / "2.夜间灯光_LongNTL_500m" / "LongNTL_2024_黄河滩区中下游边界.tif", "kind": "continuous", "colors": ((47, 56, 53), (231, 177, 51)), "resampling": Resampling.average},
}


def valid_mask(arr: np.ndarray, nodata: float | int | None) -> np.ndarray:
    mask = np.isfinite(arr)
    if nodata is not None:
        mask &= arr != nodata
    for sentinel in NODATA_SENTINELS:
        mask &= ~np.isclose(arr, sentinel)
    return mask


def ramp(values: np.ndarray, start: tuple[int, int, int], end: tuple[int, int, int]) -> np.ndarray:
    start_arr = np.array(start, dtype=np.float32)
    end_arr = np.array(end, dtype=np.float32)
    t = np.clip(values, 0, 1)[..., None]
    return (start_arr + (end_arr - start_arr) * t).astype(np.uint8)


def normalize(values: np.ndarray, valid: np.ndarray, p_low: float = 2, p_high: float = 98) -> np.ndarray:
    result = np.zeros(values.shape, dtype=np.float32)
    if not valid.any():
        return result
    data = values[valid].astype("float64")
    low, high = np.nanpercentile(data, [p_low, p_high])
    if high <= low:
        result[valid] = 0.5
        return result
    result[valid] = (values[valid] - low) / (high - low)
    return np.clip(result, 0, 1)


def colorize_continuous(path: Path, colors: tuple[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        valid = valid_mask(arr, src.nodata)
    norm = normalize(arr, valid)
    rgb = ramp(norm, colors[0], colors[1])
    alpha = np.where(valid, 235, 0).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), mode="RGBA")


def colorize_clcd(path: Path) -> Image.Image:
    palette = {1: (230, 204, 110), 2: (38, 110, 62), 3: (98, 140, 58), 4: (140, 178, 78), 5: (32, 118, 168), 6: (188, 176, 132), 7: (150, 108, 66), 8: (196, 72, 42), 9: (108, 102, 88)}
    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata
    rgba = np.zeros((*arr.shape, 4), dtype=np.uint8)
    for value, color in palette.items():
        mask = arr == value
        rgba[mask, :3] = color
        rgba[mask, 3] = 240
    if nodata is not None:
        rgba[arr == nodata, 3] = 0
    return Image.fromarray(rgba, mode="RGBA")


def colorize_water(path: Path) -> Image.Image:
    palette = {1: (158, 210, 228), 2: (28, 128, 188), 3: (8, 72, 128)}
    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata
    rgba = np.zeros((*arr.shape, 4), dtype=np.uint8)
    for value, color in palette.items():
        mask = arr == value
        rgba[mask, :3] = color
        rgba[mask, 3] = 245
    if nodata is not None:
        rgba[arr == nodata, 3] = 0
    return Image.fromarray(rgba, mode="RGBA")


def build_overlay(layer: str, spec: dict) -> Path:
    path = spec["path"]
    if not path.exists():
        raise FileNotFoundError(path)
    if spec["kind"] == "clcd":
        image = colorize_clcd(path)
    elif spec["kind"] == "water":
        image = colorize_water(path)
    else:
        image = colorize_continuous(path, spec["colors"])
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    output = OVERLAY_DIR / f"{layer}_{YEAR}.png"
    image.save(output, compress_level=1)
    return output


def build_query_grid(layer: str, spec: dict) -> Path:
    path = spec["path"]
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        data = src.read(1, out_shape=(GRID_HEIGHT, GRID_WIDTH), resampling=spec["resampling"], masked=True)
        values = data.astype("float32").filled(np.nan)
        nodata = src.nodata
        if nodata is not None:
            values[np.isclose(values, nodata)] = np.nan
        for sentinel in NODATA_SENTINELS:
            values[np.isclose(values, sentinel)] = np.nan
        payload = {
            "layer": layer,
            "year": YEAR,
            "source": str(path),
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "bounds": {"west": src.bounds.left, "south": src.bounds.bottom, "east": src.bounds.right, "north": src.bounds.top},
            "values": [[None if np.isnan(v) else round(float(v), 4) for v in row] for row in values],
        }
    QUERY_GRID_DIR.mkdir(parents=True, exist_ok=True)
    output = QUERY_GRID_DIR / f"{layer}_{YEAR}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return output


def compute_stats(layer: str, spec: dict) -> dict:
    path = spec["path"]
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        valid = valid_mask(arr, src.nodata)
        values = arr[valid]
        if values.size == 0:
            return {"available": False, "sourceYear": YEAR, "validRatio": 0, "min": None, "median": None, "p90": None, "max": None, "file": str(path)}
        q = np.nanpercentile(values.astype("float64"), [0, 50, 90, 100])
        return {"available": True, "sourceYear": YEAR, "validRatio": round(float(values.size / arr.size), 6), "min": round(float(q[0]), 4), "median": round(float(q[1]), 4), "p90": round(float(q[2]), 4), "max": round(float(q[3]), 4), "file": str(path)}


def write_stats_js(stats: dict) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    output = CONFIG_DIR / "layerStats2024.js"
    payload = json.dumps({str(YEAR): stats}, ensure_ascii=False, indent=2)
    output.write_text(f"window.LAYER_STATS_2024 = {payload};\n", encoding="utf-8")
    return output


def main() -> None:
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"SOURCE_ROOT not found: {SOURCE_ROOT}")
    print(f"source_root={SOURCE_ROOT}")
    outputs: list[Path] = []
    stats: dict = {}
    for layer, spec in LAYERS.items():
        print(f"processing {layer}: {spec['path']}")
        overlay = build_overlay(layer, spec)
        grid = build_query_grid(layer, spec)
        stats[layer] = compute_stats(layer, spec)
        outputs.extend([overlay, grid])
        print(f"  wrote {overlay.relative_to(ROOT)}")
        print(f"  wrote {grid.relative_to(ROOT)}")
        print(f"  stats median={stats[layer]['median']} valid={stats[layer]['validRatio']}")
    stats_js = write_stats_js(stats)
    outputs.append(stats_js)
    print(f"  wrote {stats_js.relative_to(ROOT)}")
    total_mb = sum(path.stat().st_size for path in outputs) / 1024 / 1024
    print(f"generated {len(outputs)} files, {total_mb:.2f} MB")


if __name__ == "__main__":
    main()
