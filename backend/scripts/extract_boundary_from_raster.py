from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_bounds, transform_geom


ROOT = Path(__file__).resolve().parents[2]
SOURCE_RASTER = (
    ROOT
    / "data"
    / "raw"
    / "智能体数据集_黄河滩区边界裁剪结果"
    / "智能体数据集_黄河滩区边界裁剪结果_最终"
    / "1.土地利用_CLCD_30m"
    / "CLCD_2025_黄河滩区中下游边界.tif"
)
OUTPUT_GEOJSON = (
    ROOT / "data" / "raw" / "boundary" / "yellow_river_floodplain_boundary.geojson"
)


def main() -> None:
    OUTPUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(SOURCE_RASTER) as src:
        data = src.read(1, masked=True)
        valid = (~data.mask) & (data.filled(0) != 0)
        binary = valid.astype(np.uint8)

        features = []
        for geom, value in shapes(binary, mask=valid, transform=src.transform):
            if value != 1:
                continue
            geom_wgs84 = transform_geom(src.crs, "EPSG:4326", geom, precision=7)
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "name": "Yellow River floodplain clipped raster boundary",
                        "source": str(SOURCE_RASTER.relative_to(ROOT)).replace("\\", "/"),
                    },
                    "geometry": geom_wgs84,
                }
            )

        bbox = transform_bounds(src.crs, "EPSG:4326", *src.bounds, densify_pts=21)

    collection = {
        "type": "FeatureCollection",
        "name": "yellow_river_floodplain_boundary",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "bbox": list(bbox),
        "features": features,
    }

    OUTPUT_GEOJSON.write_text(
        json.dumps(collection, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT_GEOJSON}")
    print(f"features {len(features)}")
    print(f"bbox_wgs84 {bbox}")


if __name__ == "__main__":
    main()
