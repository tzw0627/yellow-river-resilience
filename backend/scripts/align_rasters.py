from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "aligned"

TARGET_CRS = "EPSG:4326"
WEST = 112.177287
SOUTH = 34.237112
EAST = 116.678382
NORTH = 36.454202
TARGET_RESOLUTION = 0.00224578821

CATEGORY_NODATA = 0
CONTINUOUS_NODATA = -9999.0


def is_categorical(path: Path) -> bool:
    text = f"{path.parent.name}/{path.name}"
    return (
        "CLCD" in text
        or "土地利用" in text
        or "waterClass" in text
        or "水体" in text and "Frequency" not in text
    )


def output_stem(path: Path) -> str:
    name = path.name
    years = re.findall(r"(?:19|20)\d{2}", name)
    year_part = "_".join(years) if years else "static"

    if "CLCD" in name:
        return f"clcd_{year_part}_epsg4326_250m"
    if "LongNTL" in name:
        return f"ntl_{year_part}_epsg4326_250m"
    if "DEM" in name:
        return "dem_static_epsg4326_250m"
    if "LandScan" in name:
        return f"population_{year_part}_epsg4326_250m"
    if "GDP" in name:
        return f"gdp_{year_part}_epsg4326_250m"
    if "NDVI" in name:
        return f"ndvi_{year_part}_epsg4326_250m"
    if "EVI" in name:
        return f"evi_{year_part}_epsg4326_250m"
    if "Water_Frequency" in name:
        return f"water_frequency_{year_part}_epsg4326_250m"
    if "waterClass" in name:
        return f"water_class_{year_part}_epsg4326_250m"
    if "TerraClimate" in name:
        return f"terraclimate_{year_part}_epsg4326_250m"

    safe = re.sub(r"[^0-9A-Za-z_]+", "_", path.stem).strip("_").lower()
    return f"{safe}_epsg4326_250m"


def target_grid() -> tuple[int, int, rasterio.Affine]:
    width = math.ceil((EAST - WEST) / TARGET_RESOLUTION)
    height = math.ceil((NORTH - SOUTH) / TARGET_RESOLUTION)
    transform = from_origin(WEST, NORTH, TARGET_RESOLUTION, TARGET_RESOLUTION)
    return width, height, transform


def destination_profile(src: rasterio.DatasetReader, path: Path) -> dict:
    categorical = is_categorical(path)
    width, height, transform = target_grid()
    dtype = src.dtypes[0] if categorical else "float32"
    nodata = CATEGORY_NODATA if categorical else CONTINUOUS_NODATA
    return {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": src.count,
        "dtype": dtype,
        "crs": TARGET_CRS,
        "transform": transform,
        "nodata": nodata,
        "compress": "deflate",
        "predictor": 2 if not categorical else 1,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF": "IF_SAFER",
    }


def align_one(path: Path) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{output_stem(path)}.tif"

    categorical = is_categorical(path)
    resampling = Resampling.nearest if categorical else Resampling.bilinear

    with rasterio.open(path) as src:
        profile = destination_profile(src, path)
        src_nodata = src.nodata
        dst_nodata = profile["nodata"]

        with rasterio.open(output_path, "w", **profile) as dst:
            for band_index in range(1, src.count + 1):
                destination = np.full(
                    (profile["height"], profile["width"]),
                    dst_nodata,
                    dtype=profile["dtype"],
                )
                reproject(
                    source=rasterio.band(src, band_index),
                    destination=destination,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src_nodata,
                    dst_transform=profile["transform"],
                    dst_crs=profile["crs"],
                    dst_nodata=dst_nodata,
                    resampling=resampling,
                )
                dst.write(destination, band_index)
                if src.descriptions and src.descriptions[band_index - 1]:
                    dst.set_band_description(
                        band_index, src.descriptions[band_index - 1]
                    )

    return output_path


def main() -> None:
    tif_paths = sorted(
        p for p in RAW_DIR.rglob("*.tif") if "data\\processed" not in str(p)
    )
    print(f"target_crs {TARGET_CRS}")
    print(f"target_resolution {TARGET_RESOLUTION}")
    print(f"target_bbox {WEST},{SOUTH},{EAST},{NORTH}")
    print(f"input_rasters {len(tif_paths)}")

    for index, path in enumerate(tif_paths, start=1):
        output = align_one(path)
        print(f"[{index}/{len(tif_paths)}] {path.name} -> {output.name}")


if __name__ == "__main__":
    main()
