from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ALIGNED_DIR = ROOT / "data" / "processed" / "aligned"
INDEX_DIR = ROOT / "data" / "processed" / "indices"
OVERLAY_DIR = ROOT / "frontend" / "data" / "overlays"

YEARS = [2000, 2005, 2010, 2015, 2020, 2025]


def ramp(values: np.ndarray, start: tuple[int, int, int], end: tuple[int, int, int]) -> np.ndarray:
    start_arr = np.array(start, dtype=np.float32)
    end_arr = np.array(end, dtype=np.float32)
    t = np.clip(values, 0, 1)[..., None]
    return (start_arr + (end_arr - start_arr) * t).astype(np.uint8)


def normalize(values: np.ndarray, valid: np.ndarray, p_low: float = 2, p_high: float = 98) -> np.ndarray:
    result = np.zeros(values.shape, dtype=np.float32)
    if not valid.any():
        return result
    low, high = np.nanpercentile(values[valid].astype("float64"), [p_low, p_high])
    if high <= low:
        return result
    result[valid] = (values[valid] - low) / (high - low)
    return np.clip(result, 0, 1)


def colorize_continuous(path: Path, start: tuple[int, int, int], end: tuple[int, int, int]) -> Image.Image:
    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata
    valid = np.isfinite(arr)
    if nodata is not None:
        valid &= arr != nodata
    norm = normalize(arr, valid)
    rgb = ramp(norm, start, end)
    alpha = np.where(valid, 235, 0).astype(np.uint8)
    rgba = np.dstack([rgb, alpha])
    return Image.fromarray(rgba, mode="RGBA")


def colorize_clcd(path: Path) -> Image.Image:
    palette = {
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
    palette = {
        1: (158, 210, 228),
        2: (28, 128, 188),
        3: (8, 72, 128),
    }
    with rasterio.open(path) as src:
        arr = src.read(1)
    rgba = np.zeros((*arr.shape, 4), dtype=np.uint8)
    for value, color in palette.items():
        mask = arr == value
        rgba[mask, :3] = color
        rgba[mask, 3] = 245
    return Image.fromarray(rgba, mode="RGBA")


def source_path(layer: str, year: int) -> Path:
    if layer == "ndvi":
        return ALIGNED_DIR / f"ndvi_{year}_epsg4326_250m.tif"
    if layer == "evi":
        return ALIGNED_DIR / f"evi_{year}_epsg4326_250m.tif"
    if layer == "clcd":
        return ALIGNED_DIR / f"clcd_{year}_epsg4326_250m.tif"
    if layer == "water":
        if year == 2025:
            return ALIGNED_DIR / "water_class_2025_2021_epsg4326_250m.tif"
        return ALIGNED_DIR / f"water_class_{year}_{year}_epsg4326_250m.tif"
    if layer == "ntl":
        actual = 2024 if year == 2025 else year
        return ALIGNED_DIR / f"ntl_{actual}_epsg4326_250m.tif"
    if layer == "gdp":
        actual = 2023 if year == 2025 else year
        return ALIGNED_DIR / f"gdp_{actual}_epsg4326_250m.tif"
    if layer == "ri":
        return INDEX_DIR / "resilience_index_2025.tif"
    raise ValueError(layer)


def build_overlay(layer: str, year: int) -> Path:
    path = source_path(layer, year)
    if layer == "clcd":
        image = colorize_clcd(path)
    elif layer == "water":
        image = colorize_water(path)
    elif layer == "ntl":
        image = colorize_continuous(path, (47, 56, 53), (231, 177, 51))
    elif layer == "gdp":
        image = colorize_continuous(path, (89, 69, 46), (214, 145, 75))
    elif layer == "ri":
        image = colorize_continuous(path, (174, 65, 52), (74, 142, 79))
    elif layer == "evi":
        image = colorize_continuous(path, (214, 221, 169), (36, 132, 91))
    else:
        image = colorize_continuous(path, (218, 222, 170), (87, 130, 51))

    output = OVERLAY_DIR / f"{layer}_{year}.png"
    image.save(output, compress_level=1)
    return output


def main() -> None:
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for layer in ["ndvi", "evi", "clcd", "water", "ntl", "gdp"]:
        for year in YEARS:
            output = build_overlay(layer, year)
            outputs.append(output)
            print(output.relative_to(ROOT))
    output = build_overlay("ri", 2025)
    outputs.append(output)
    print(output.relative_to(ROOT))
    total_mb = sum(p.stat().st_size for p in outputs) / 1024 / 1024
    print(f"generated {len(outputs)} overlays, {total_mb:.2f} MB")


if __name__ == "__main__":
    main()
