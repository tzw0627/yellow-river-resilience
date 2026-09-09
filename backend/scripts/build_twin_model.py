from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds


ROOT = Path(__file__).resolve().parents[2]
ALIGNED_DIR = ROOT / "data" / "processed" / "aligned"
INDEX_DIR = ROOT / "data" / "processed" / "indices"
OUTPUT = ROOT / "frontend" / "data" / "twin_model.json"

SEGMENTS = [
    {
        "id": "luoyang",
        "name": "洛阳段",
        "bbox": [112.177287, 34.55, 112.72, 35.18],
        "description": "研究区西部入口段，包含孟津等代表站点。",
    },
    {
        "id": "jiaozuo_zhengzhou",
        "name": "焦作-郑州段",
        "bbox": [112.72, 34.45, 113.55, 35.25],
        "description": "黄河中下游过渡段，包含孟州、温县、巩义等代表站点。",
    },
    {
        "id": "xinxiang",
        "name": "新乡段",
        "bbox": [113.55, 34.75, 115.05, 35.55],
        "description": "滩区核心分析段，包含原阳、封丘、长垣等代表站点。",
    },
    {
        "id": "puyang",
        "name": "濮阳段",
        "bbox": [115.05, 35.35, 116.678382, 36.454202],
        "description": "研究区东部下游段，包含台前等代表站点。",
    },
]

STATIONS = [
    {"id": "53983", "name": "封丘", "county": "封丘县", "city": "新乡市", "lat": 35.05, "lon": 114.433333333333},
    {"id": "53989", "name": "原阳", "county": "原阳县", "city": "新乡市", "lat": 35.05, "lon": 113.95},
    {"id": "53998", "name": "长垣", "county": "长垣县", "city": "新乡市", "lat": 35.2, "lon": 114.666666666667},
    {"id": "54817", "name": "台前", "county": "台前县", "city": "濮阳市", "lat": 35.9833333333333, "lon": 115.866666666667},
    {"id": "57071", "name": "孟津", "county": "孟津县", "city": "洛阳市", "lat": 34.8333333333333, "lon": 112.433333333333},
    {"id": "57072", "name": "孟州", "county": "孟州市", "city": "焦作市", "lat": 34.9166666666667, "lon": 112.783333333333},
    {"id": "57079", "name": "温县", "county": "温县", "city": "焦作市", "lat": 34.95, "lon": 113.083333333333},
    {"id": "57080", "name": "巩义", "county": "巩义市", "city": "郑州市", "lat": 34.7333333333333, "lon": 112.966666666667},
]

LAYERS = {
    "ndvi": {"name": "NDVI", "path": ALIGNED_DIR / "ndvi_2025_epsg4326_250m.tif"},
    "evi": {"name": "EVI", "path": ALIGNED_DIR / "evi_2025_epsg4326_250m.tif"},
    "water": {"name": "水体", "path": ALIGNED_DIR / "water_frequency_2000_2021_epsg4326_250m.tif"},
    "ntl": {"name": "夜间灯光", "path": ALIGNED_DIR / "ntl_2024_epsg4326_250m.tif"},
    "gdp": {"name": "GDP", "path": ALIGNED_DIR / "gdp_2023_epsg4326_250m.tif"},
    "ri": {"name": "生态韧性指数", "path": INDEX_DIR / "resilience_index_2025.tif"},
}


def raster_stats(path: Path, bbox: list[float] | None = None) -> dict[str, float | int | None]:
    with rasterio.open(path) as src:
        if bbox:
            window = from_bounds(*bbox, transform=src.transform)
            arr = src.read(1, window=window, masked=True)
        else:
            arr = src.read(1, masked=True)
        values = arr.compressed().astype("float64")
        if values.size == 0:
            return {"mean": None, "median": None, "p90": None, "valid": 0}
        q = np.nanpercentile(values, [50, 90])
        return {
            "mean": round(float(np.nanmean(values)), 4),
            "median": round(float(q[0]), 4),
            "p90": round(float(q[1]), 4),
            "valid": int(values.size),
        }


def classify_ri(value: float | None) -> str:
    if value is None:
        return "暂无数据"
    if value >= 0.75:
        return "高韧性"
    if value >= 0.55:
        return "中韧性"
    return "低韧性"


def build_state(bbox: list[float] | None = None) -> dict:
    state = {}
    for key, layer in LAYERS.items():
        state[key] = raster_stats(layer["path"], bbox)
    ri = state["ri"]["median"]
    state["summary"] = {
        "level": classify_ri(ri),
        "text": f"2025 年生态韧性状态为{classify_ri(ri)}，RI 中位数为 {ri if ri is not None else '--'}。",
    }
    return state


def main() -> None:
    twin = {
        "schema": "hpu-yellow-river-twin-v1",
        "year": 2025,
        "region": {
            "id": "yellow_river_floodplain_mid_lower",
            "type": "TwinRegion",
            "name": "黄河滩区中下游研究区",
            "bbox": [112.177287, 34.237112, 116.678382, 36.454202],
            "state": build_state(),
        },
        "segments": [],
        "stations": STATIONS,
        "layers": [
            {"id": key, "type": "TwinLayer", "name": layer["name"]}
            for key, layer in LAYERS.items()
        ],
    }
    for segment in SEGMENTS:
        twin["segments"].append(
            {
                **segment,
                "type": "TwinSegment",
                "stations": [
                    s["id"]
                    for s in STATIONS
                    if segment["bbox"][0] <= s["lon"] <= segment["bbox"][2]
                    and segment["bbox"][1] <= s["lat"] <= segment["bbox"][3]
                ],
                "state": build_state(segment["bbox"]),
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(twin, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"segments {len(twin['segments'])}")


if __name__ == "__main__":
    main()
