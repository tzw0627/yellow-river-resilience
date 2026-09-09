from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling


ROOT = Path(__file__).resolve().parents[2]
ALIGNED_DIR = ROOT / "data" / "processed" / "aligned"
INDEX_DIR = ROOT / "data" / "processed" / "indices"
OUTPUT_DIR = ROOT / "frontend" / "data" / "query_grids"

YEARS = [2000, 2005, 2010, 2015, 2020, 2025]
GRID_WIDTH = 200
GRID_HEIGHT = 99


def source_path(layer: str, year: int) -> Path | None:
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
        return INDEX_DIR / "resilience_index_2025.tif" if year == 2025 else None
    return None


def resampling_for(layer: str) -> Resampling:
    if layer in {"clcd", "water"}:
        return Resampling.nearest
    return Resampling.average


def build_grid(layer: str, year: int) -> Path | None:
    path = source_path(layer, year)
    if path is None or not path.exists():
        return None

    with rasterio.open(path) as src:
        data = src.read(
            1,
            out_shape=(GRID_HEIGHT, GRID_WIDTH),
            resampling=resampling_for(layer),
            masked=True,
        )
        values = data.astype("float32").filled(np.nan)
        nodata = src.nodata
        if nodata is not None:
            values[np.isclose(values, nodata)] = np.nan
        payload = {
            "layer": layer,
            "year": year,
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "bounds": {
                "west": src.bounds.left,
                "south": src.bounds.bottom,
                "east": src.bounds.right,
                "north": src.bounds.top,
            },
            "values": [
                [None if np.isnan(v) else round(float(v), 4) for v in row]
                for row in values
            ],
        }

    output = OUTPUT_DIR / f"{layer}_{year}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for layer in ["ndvi", "evi", "clcd", "water", "ntl", "gdp", "ri"]:
        for year in YEARS:
            output = build_grid(layer, year)
            if output:
                outputs.append(output)
                print(output.relative_to(ROOT))
    total_mb = sum(p.stat().st_size for p in outputs) / 1024 / 1024
    print(f"generated {len(outputs)} query grids, {total_mb:.2f} MB")


if __name__ == "__main__":
    main()
