from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[2]
ALIGNED_DIR = ROOT / "data" / "processed" / "aligned"
BOUNDARY_SOURCE = ROOT / "data" / "raw" / "boundary" / "yellow_river_floodplain_boundary.geojson"
FRONTEND_DATA = ROOT / "frontend" / "data"

YEARS = [2000, 2005, 2010, 2015, 2020, 2025]
LAYERS = {
    "ndvi": {
        "label": "NDVI",
        "unit": "",
        "description": "植被覆盖和生态质量的核心遥感指标。",
        "pattern": "ndvi_{year}_epsg4326_250m.tif",
    },
    "evi": {
        "label": "EVI",
        "unit": "",
        "description": "植被活力指标，对高覆盖植被区更敏感。",
        "pattern": "evi_{year}_epsg4326_250m.tif",
    },
    "clcd": {
        "label": "CLCD",
        "unit": "class",
        "description": "土地利用分类，用于识别耕地、建设用地、水体和生态空间变化。",
        "pattern": "clcd_{year}_epsg4326_250m.tif",
    },
    "water": {
        "label": "Water",
        "unit": "class",
        "description": "JRC 水体分类，用于判断水域分布和洪泛背景。",
        "pattern": "water_class_{year}_{year}_epsg4326_250m.tif",
        "special": "water_class",
        "fallback": {2025: 2021},
    },
    "ntl": {
        "label": "Night Light",
        "unit": "",
        "description": "夜间灯光强度，用于近似表征人类活动和建设开发压力。",
        "pattern": "ntl_{year}_epsg4326_250m.tif",
        "fallback": {2025: 2024},
    },
    "gdp": {
        "label": "GDP",
        "unit": "",
        "description": "空间化 GDP，用于社会经济适应能力分析。",
        "pattern": "gdp_{year}_epsg4326_250m.tif",
        "fallback": {2025: 2023, 2024: 2023},
    },
    "ri": {
        "label": "Resilience Index",
        "unit": "",
        "description": "MVP 生态韧性综合指数，由抵抗力、恢复力和适应力分量综合得到。",
        "pattern": "../indices/resilience_index_2025.tif",
        "only_years": [2025],
    },
}


def raster_stats(path: Path) -> dict[str, float | int | str]:
    with rasterio.open(path) as ds:
        arr = ds.read(1, masked=True)
        values = arr.compressed().astype("float64")
        if values.size == 0:
            return {
                "validRatio": 0,
                "min": None,
                "median": None,
                "max": None,
                "p90": None,
            }
        q = np.nanpercentile(values, [0, 50, 90, 100])
        return {
            "validRatio": round(float(values.size / arr.size), 4),
            "min": round(float(q[0]), 4),
            "median": round(float(q[1]), 4),
            "p90": round(float(q[2]), 4),
            "max": round(float(q[3]), 4),
        }


def resolve_layer_path(layer: dict, year: int) -> tuple[Path | None, int | None]:
    if "only_years" in layer and year not in layer["only_years"]:
        return None, None
    if layer.get("pattern", "").startswith("../indices/"):
        path = (ALIGNED_DIR / layer["pattern"]).resolve()
        if path.exists():
            return path, year
        return None, None
    actual_year = layer.get("fallback", {}).get(year, year)
    if layer.get("special") == "water_class" and year == 2025:
        path = ALIGNED_DIR / "water_class_2025_2021_epsg4326_250m.tif"
    else:
        path = ALIGNED_DIR / layer["pattern"].format(year=actual_year)
    if path.exists():
        return path, actual_year
    return None, None


def build_summary() -> dict:
    summary = {
        "bounds": {
            "west": 112.177287,
            "south": 34.237112,
            "east": 116.678382,
            "north": 36.454202,
            "center": [114.427835, 35.345657],
        },
        "years": YEARS,
        "layers": [],
        "timeline": {},
    }
    for key, layer in LAYERS.items():
        summary["layers"].append(
            {
                "id": key,
                "label": layer["label"],
                "unit": layer["unit"],
                "description": layer["description"],
            }
        )
    for year in YEARS:
        year_entry = {}
        for key, layer in LAYERS.items():
            path, actual_year = resolve_layer_path(layer, year)
            if not path:
                year_entry[key] = {"available": False}
                continue
            stats = raster_stats(path)
            stats.update(
                {
                    "available": True,
                    "sourceYear": actual_year,
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                }
            )
            year_entry[key] = stats
        summary["timeline"][str(year)] = year_entry
    return summary


def write_boundary_display(step: int = 10) -> None:
    data = json.loads(BOUNDARY_SOURCE.read_text(encoding="utf-8"))

    def decimate_ring(ring: list[list[float]]) -> list[list[float]]:
        if len(ring) <= 240:
            return ring
        sampled = ring[::step]
        if sampled[-1] != ring[-1]:
            sampled.append(ring[-1])
        return sampled

    for feature in data["features"]:
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            geometry["coordinates"] = [decimate_ring(ring) for ring in geometry["coordinates"]]
        elif geometry["type"] == "MultiPolygon":
            geometry["coordinates"] = [
                [decimate_ring(ring) for ring in polygon] for polygon in geometry["coordinates"]
            ]

    (FRONTEND_DATA / "boundary_display.geojson").write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    FRONTEND_DATA.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BOUNDARY_SOURCE, FRONTEND_DATA / "boundary.geojson")
    write_boundary_display()
    summary = build_summary()
    (FRONTEND_DATA / "layer_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {FRONTEND_DATA / 'boundary.geojson'}")
    print(f"wrote {FRONTEND_DATA / 'boundary_display.geojson'}")
    print(f"wrote {FRONTEND_DATA / 'layer_summary.json'}")


if __name__ == "__main__":
    main()
