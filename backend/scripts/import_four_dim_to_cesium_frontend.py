from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject, transform_geom


ROOT = Path(__file__).resolve().parents[2]
NODATA = -9999.0
GRID_WIDTH = 200
GRID_HEIGHT = 99

LAYER_META = {
    "er": {
        "id": "four_dim_er",
        "name": "四维综合生态韧性 ER",
        "unit": "0-1",
        "description": "综合规模、密度、形态与洪水韧性的四维生态韧性指数。",
        "direction": "higher_is_better",
        "colors": ((168, 55, 48), (226, 190, 86), (54, 132, 88)),
    },
    "ers": {
        "id": "four_dim_ers",
        "name": "规模韧性 ERS",
        "unit": "0-1",
        "description": "生态基础设施规模相对建设压力的韧性表现，值越高表示规模韧性越强。",
        "direction": "higher_is_better",
        "colors": ((188, 80, 59), (220, 191, 92), (64, 139, 80)),
    },
    "erd": {
        "id": "four_dim_erd",
        "name": "密度韧性 ERD",
        "unit": "0-1",
        "description": "生态承载能力相对人口、GDP 与夜间灯光压力的韧性表现。",
        "direction": "higher_is_better",
        "colors": ((174, 71, 55), (219, 182, 85), (63, 127, 103)),
    },
    "erm": {
        "id": "four_dim_erm",
        "name": "形态韧性 ERM",
        "unit": "0-1",
        "description": "建设源到生态汇的距离衰减韧性，值越高表示更接近生态斑块或生态汇。",
        "direction": "higher_is_better",
        "colors": ((150, 73, 74), (210, 178, 99), (54, 127, 116)),
    },
    "erf": {
        "id": "four_dim_erf",
        "name": "洪水韧性 ERF",
        "unit": "0-1",
        "description": "由洪水风险反向得到，值越高表示洪水韧性越强。",
        "direction": "higher_is_better",
        "colors": ((162, 61, 58), (216, 184, 96), (51, 126, 139)),
    },
    "fri": {
        "id": "four_dim_fri",
        "name": "洪水风险 FRI",
        "unit": "0-1",
        "description": "综合相对高程、坡度、水体发生率和土地覆盖风险，值越高表示洪水风险越高。",
        "direction": "higher_is_risk",
        "colors": ((49, 107, 151), (231, 190, 99), (182, 55, 48)),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import four-dimensional GeoTIFFs into Cesium frontend data.")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "processed" / "four_dim_manual")
    parser.add_argument("--overlay-output", type=Path, default=ROOT / "frontend" / "data" / "overlays" / "four_dim")
    parser.add_argument("--query-output", type=Path, default=ROOT / "frontend" / "data" / "query_grids" / "four_dim")
    parser.add_argument("--summary", type=Path, default=ROOT / "frontend" / "data" / "layer_summary.json")
    parser.add_argument(
        "--reference",
        type=Path,
        default=ROOT / "data" / "processed" / "aligned" / "clcd_2020_epsg4326_250m.tif",
        help="Reference raster whose CRS, transform, dimensions, resolution and bounds define the output grid.",
    )
    parser.add_argument(
        "--boundary",
        type=Path,
        default=ROOT / "frontend" / "data" / "boundary.geojson",
        help="Study-area boundary used to mask pixels outside the research area.",
    )
    parser.add_argument(
        "--aligned-output",
        type=Path,
        default=ROOT / "data" / "processed" / "four_dim_aligned",
        help="Aligned and boundary-masked GeoTIFF output directory.",
    )
    return parser.parse_args()


def valid_data(path: Path) -> tuple[np.ndarray, np.ndarray, dict, object]:
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        nodata = src.nodata
        valid = np.isfinite(arr)
        if nodata is not None:
            valid &= arr != nodata
        arr[~valid] = np.nan
        profile = src.profile.copy()
        bounds = src.bounds
    return arr, valid, profile, bounds


def _geojson_geometries(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("type") == "FeatureCollection":
        return [feature["geometry"] for feature in data.get("features", []) if feature.get("geometry")]
    if data.get("type") == "Feature":
        geometry = data.get("geometry")
        return [geometry] if geometry else []
    return [data]


def load_boundary_geometries(boundary_path: Path, dst_crs) -> list[dict]:
    geometries = _geojson_geometries(boundary_path)
    if not geometries:
        raise RuntimeError(f"No geometry found in study-area boundary: {boundary_path}")
    return [transform_geom("EPSG:4326", dst_crs, geometry) for geometry in geometries]


def align_and_mask(src_path: Path, reference, boundary_geometries: list[dict], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src_path) as src:
        destination = np.full((reference.height, reference.width), NODATA, dtype="float32")
        reproject(
            source=rasterio.band(src, 1),
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=reference.transform,
            dst_crs=reference.crs,
            dst_nodata=NODATA,
            resampling=Resampling.bilinear,
        )
        inside = geometry_mask(
            boundary_geometries,
            out_shape=(reference.height, reference.width),
            transform=reference.transform,
            invert=True,
            all_touched=False,
        )
        destination[~inside] = NODATA
        destination[~np.isfinite(destination)] = NODATA
        profile = reference.profile.copy()
        profile.update(
            driver="GTiff",
            count=1,
            dtype="float32",
            nodata=NODATA,
            compress="lzw",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            BIGTIFF="IF_SAFER",
        )
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(destination, 1)
            desc = src.descriptions[0] if src.descriptions else None
            if desc:
                dst.set_band_description(1, desc)
    return output_path


def ramp3(values: np.ndarray, low: tuple[int, int, int], mid: tuple[int, int, int], high: tuple[int, int, int]) -> np.ndarray:
    t = np.clip(values, 0, 1)
    rgb = np.zeros((*values.shape, 3), dtype=np.float32)
    lower = t <= 0.5
    upper = ~lower
    low_a = np.array(low, dtype=np.float32)
    mid_a = np.array(mid, dtype=np.float32)
    high_a = np.array(high, dtype=np.float32)
    rgb[lower] = low_a + (mid_a - low_a) * (t[lower][..., None] * 2)
    rgb[upper] = mid_a + (high_a - mid_a) * ((t[upper][..., None] - 0.5) * 2)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def colorize(path: Path, key: str, output: Path) -> None:
    arr, valid, _, _ = valid_data(path)
    low, mid, high = LAYER_META[key]["colors"]
    values = np.where(valid, np.clip(arr, 0, 1), 0)
    rgb = ramp3(values, low, mid, high)
    alpha = np.where(valid, 238, 0).astype(np.uint8)
    rgba = np.dstack([rgb, alpha])
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba).save(output, compress_level=1)


def build_query_grid(path: Path, key: str, year: int, output: Path) -> None:
    with rasterio.open(path) as src:
        data = src.read(1, out_shape=(GRID_HEIGHT, GRID_WIDTH), resampling=Resampling.average, masked=True)
        values = data.astype("float32").filled(np.nan)
        nodata = src.nodata
        if nodata is not None:
            values[np.isclose(values, nodata)] = np.nan
        payload = {
            "layer": LAYER_META[key]["id"],
            "year": year,
            "source": str(path),
            "width": GRID_WIDTH,
            "height": GRID_HEIGHT,
            "bounds": {
                "west": src.bounds.left,
                "south": src.bounds.bottom,
                "east": src.bounds.right,
                "north": src.bounds.top,
            },
            "values": [[None if np.isnan(v) else round(float(v), 4) for v in row] for row in values],
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def stats(arr: np.ndarray, valid: np.ndarray) -> dict[str, float | int]:
    values = arr[valid]
    if values.size == 0:
        return {
            "min": math.nan,
            "max": math.nan,
            "mean": math.nan,
            "median": math.nan,
            "p90": math.nan,
            "valid_count": 0,
            "valid_ratio": 0.0,
        }
    return {
        "min": round(float(np.nanmin(values)), 4),
        "max": round(float(np.nanmax(values)), 4),
        "mean": round(float(np.nanmean(values)), 4),
        "median": round(float(np.nanmedian(values)), 4),
        "p90": round(float(np.nanpercentile(values, 90)), 4),
        "valid_count": int(values.size),
        "valid_ratio": round(float(values.size / arr.size), 6),
    }


def ensure_layer(summary: dict, key: str) -> None:
    layer_id = LAYER_META[key]["id"]
    if any(layer["id"] == layer_id for layer in summary.get("layers", [])):
        return
    summary.setdefault("layers", []).append(
        {
            "id": layer_id,
            "label": LAYER_META[key]["name"],
            "unit": LAYER_META[key]["unit"],
            "description": LAYER_META[key]["description"],
            "direction": LAYER_META[key]["direction"],
        }
    )


def relative(path: Path) -> str:
    return path.resolve().relative_to((ROOT / "frontend").resolve()).as_posix()


def update_summary(summary_path: Path, entries: list[dict]) -> None:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    existing_years = set(summary.get("years", []))
    for entry in entries:
        existing_years.add(entry["year"])
    summary["years"] = sorted(existing_years)
    for key in LAYER_META:
        ensure_layer(summary, key)
    timeline = summary.setdefault("timeline", {})
    for entry in entries:
        year_obj = timeline.setdefault(str(entry["year"]), {})
        layer_id = LAYER_META[entry["key"]]["id"]
        year_obj[layer_id] = {
            "id": layer_id,
            "name": LAYER_META[entry["key"]]["name"],
            "year": entry["year"],
            "png_path": entry["png_path"],
            "query_grid_path": entry["query_grid_path"],
            "overlay": entry["png_path"],
            "queryGrid": entry["query_grid_path"],
            "bounds": entry["bounds"],
            "min": entry["min"],
            "max": entry["max"],
            "mean": entry["mean"],
            "median": entry["median"],
            "p90": entry["p90"],
            "valid_count": entry["valid_count"],
            "validRatio": entry["valid_ratio"],
            "valid_ratio": entry["valid_ratio"],
            "unit": LAYER_META[entry["key"]]["unit"],
            "description": LAYER_META[entry["key"]]["description"],
            "direction": LAYER_META[entry["key"]]["direction"],
            "available": True,
            "sourceYear": entry["year"],
            "file": entry["source"],
        }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    entries = []
    with rasterio.open(args.reference) as reference:
        boundary_geometries = load_boundary_geometries(args.boundary, reference.crs)
        reference_bounds = reference.bounds
        for year_dir in sorted(p for p in args.input.iterdir() if p.is_dir() and p.name.isdigit()):
            year = int(year_dir.name)
            aligned_year_dir = args.aligned_output / str(year)
            for key in LAYER_META:
                tif = year_dir / f"{key}_{year}.tif"
                if not tif.exists():
                    continue
                aligned_tif = aligned_year_dir / f"{key}_{year}.tif"
                align_and_mask(tif, reference, boundary_geometries, aligned_tif)
                png = args.overlay_output / f"{LAYER_META[key]['id']}_{year}.png"
                grid = args.query_output / f"{LAYER_META[key]['id']}_{year}.json"
                colorize(aligned_tif, key, png)
                build_query_grid(aligned_tif, key, year, grid)
                arr, valid, _, bounds = valid_data(aligned_tif)
                entry = {
                    "key": key,
                    "year": year,
                    "source": str(aligned_tif.resolve().relative_to(ROOT.resolve())),
                    "png_path": relative(png),
                    "query_grid_path": relative(grid),
                    "bounds": {"west": bounds.left, "south": bounds.bottom, "east": bounds.right, "north": bounds.top},
                }
                entry.update(stats(arr, valid))
                entries.append(entry)
                print(
                    f"{LAYER_META[key]['id']} {year}: {entry['png_path']} {entry['query_grid_path']} "
                    f"bounds={entry['bounds']} size={reference.width}x{reference.height}"
                )
        print(f"reference bounds: {reference_bounds}; transform: {tuple(reference.transform)}")
    update_summary(args.summary, entries)
    print(f"updated {args.summary.resolve().relative_to(ROOT.resolve())} with {len(entries)} four-dimensional layer-year entries")


if __name__ == "__main__":
    main()
