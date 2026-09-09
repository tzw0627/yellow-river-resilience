from __future__ import annotations

import argparse
import csv
import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "data" / "processed" / "four_dim_manual"
NODATA = -9999.0
EPS = 1.0e-6
DEFAULT_YEARS = [2020]
FORMAL_YEARS = [2000, 2005, 2010, 2015, 2020, 2024]

CLCD_CLASSES = {
    1: "耕地",
    2: "林地",
    3: "灌木",
    4: "草地",
    5: "水体",
    6: "冰雪",
    7: "裸地",
    8: "建设用地",
    9: "湿地",
}

ECC_WEIGHTS = {
    1: 0.50,
    2: 1.00,
    3: 0.60,
    4: 0.70,
    5: 0.90,
    6: 0.10,
    7: 0.20,
    8: 0.05,
    9: 1.00,
}

LAND_RISK_WEIGHTS = {
    1: 0.30,
    2: 0.10,
    3: 0.15,
    4: 0.20,
    5: 0.00,
    6: 0.10,
    7: 0.25,
    8: 0.40,
    9: 0.15,
}

KEYWORDS = {
    "clcd": ["clcd", "土地利用", "land", "cover"],
    "ndvi": ["ndvi"],
    "evi": ["evi"],
    "dem": ["dem", "srtm", "nasa"],
    "water": ["jrc", "water", "frequency", "水体", "occurrence"],
    "ntl": ["night", "light", "longntl", "ntl", "灯光"],
    "population": ["landscan", "population", "pop", "人口"],
    "gdp": ["gdp"],
    "terraclimate": ["terraclimate"],
}


@dataclass
class RasterSpec:
    path: Path | None
    source_year: int | str | None = None
    warning: str | None = None


def log_warning(messages: list[str], message: str) -> None:
    messages.append(message)
    warnings.warn(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate four-dimensional ecological resilience indices.")
    parser.add_argument("--input", required=True, type=Path, help="Local clipped dataset directory.")
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS, help="Years to calculate.")
    parser.add_argument(
        "--reference",
        type=Path,
        default=ROOT / "data" / "processed" / "aligned" / "clcd_2020_epsg4326_250m.tif",
        help="Reference raster used for CRS, transform, bounds, resolution and output dimensions.",
    )
    return parser.parse_args()


def tokenize(path: Path) -> str:
    return str(path).lower()


def year_score(path: Path, target_year: int, layer: str) -> tuple[int, int]:
    name = path.name.lower()
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", name)]
    if layer == "gdp" and target_year == 2024 and 2023 in years:
        return (0, 0)
    if layer == "water" and target_year == 2024 and (2024 in years or 2021 in years):
        return (0, 0 if 2024 in years else 1)
    if target_year in years:
        return (0, 0)
    if not years:
        return (1, 9999)
    return (2, min(abs(y - target_year) for y in years))


def matches(path: Path, layer: str) -> bool:
    text = tokenize(path)
    return any(keyword.lower() in text for keyword in KEYWORDS[layer])


def pick_file(files: list[Path], layer: str, year: int) -> RasterSpec:
    candidates = [p for p in files if matches(p, layer)]
    if layer == "water":
        frequency = [p for p in candidates if any(k in tokenize(p) for k in ["frequency", "occurrence"])]
        if frequency:
            candidates = frequency
    if layer == "dem":
        candidates = [p for p in candidates if "dem" in tokenize(p) or "nasa" in tokenize(p) or "srtm" in tokenize(p)]
    if not candidates:
        return RasterSpec(None, warning=f"{year}: missing {layer}")
    ranked = sorted(candidates, key=lambda p: (year_score(p, year, layer), len(str(p))))
    picked = ranked[0]
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", picked.name)]
    source_year = years[0] if years else "static"
    warning = None
    if layer == "gdp" and year == 2024 and 2023 in years:
        source_year = 2023
        warning = "2024 GDP uses 2023 source."
    if layer == "water" and year == 2024 and 2021 in years:
        source_year = 2021
        warning = "2024 water uses 2021 JRC source."
    return RasterSpec(picked, source_year=source_year, warning=warning)


def build_inventory(input_dir: Path, year: int) -> dict[str, RasterSpec]:
    files = sorted(input_dir.rglob("*.tif"))
    inventory = {layer: pick_file(files, layer, year) for layer in KEYWORDS}
    return inventory


def choose_template(inventory: dict[str, RasterSpec], reference: Path | None = None) -> Path:
    if reference is not None and reference.exists():
        return reference
    for key in ["clcd", "dem", "evi", "ndvi"]:
        path = inventory[key].path
        if path and path.exists():
            return path
    raise RuntimeError("No template raster found; expected EVI, NDVI, or CLCD.")


def read_aligned(path: Path, template: rasterio.DatasetReader, resampling: Resampling) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(path) as src:
        dst = np.full((template.height, template.width), NODATA, dtype="float32")
        src_nodata = src.nodata
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src_nodata,
            dst_transform=template.transform,
            dst_crs=template.crs,
            dst_nodata=NODATA,
            resampling=resampling,
        )
    valid = np.isfinite(dst) & (dst != NODATA)
    return dst.astype("float32"), valid


def clean_vi(values: np.ndarray, valid: np.ndarray, label: str, messages: list[str]) -> tuple[np.ndarray, np.ndarray]:
    out = values.astype("float32").copy()
    finite = valid & np.isfinite(out)
    if finite.any() and np.nanmax(out[finite]) > 2:
        out[finite] *= 0.0001
        log_warning(messages, f"{label}: max > 2, scaled by 0.0001.")
    finite = finite & (out >= -1.0) & (out <= 1.0)
    out[~finite] = np.nan
    return out, finite


def robust_norm(values: np.ndarray, valid: np.ndarray, name: str, messages: list[str], invert: bool = False) -> np.ndarray:
    out = np.zeros(values.shape, dtype="float32")
    mask = valid & np.isfinite(values)
    if not mask.any():
        log_warning(messages, f"{name}: no valid pixels; normalized to 0.")
        return out
    sample = values[mask].astype("float64")
    p2, p98 = np.nanpercentile(sample, [2, 98])
    if not np.isfinite(p2) or not np.isfinite(p98) or p98 <= p2:
        p2 = float(np.nanmin(sample))
        p98 = float(np.nanmax(sample))
        log_warning(messages, f"{name}: p2/p98 unusable; fell back to min-max.")
    if not np.isfinite(p2) or not np.isfinite(p98) or p98 <= p2:
        log_warning(messages, f"{name}: min/max unusable; normalized to 0.")
        return out
    out[mask] = ((values[mask] - p2) / (p98 - p2)).astype("float32")
    out = np.clip(out, 0, 1)
    if invert:
        out[mask] = 1 - out[mask]
    out[~mask] = np.nan
    return out


def weighted_average(parts: list[tuple[np.ndarray, np.ndarray, float, str]], messages: list[str], label: str) -> np.ndarray:
    if not parts:
        raise RuntimeError(f"{label}: no parts available.")
    shape = parts[0][0].shape
    weighted = np.zeros(shape, dtype="float32")
    weights = np.zeros(shape, dtype="float32")
    missing = []
    for arr, valid, weight, name in parts:
        if arr is None or valid is None or not valid.any():
            missing.append(name)
            continue
        mask = valid & np.isfinite(arr)
        weighted[mask] += arr[mask] * weight
        weights[mask] += weight
    if missing:
        log_warning(messages, f"{label}: missing/nonvalid variables reweighted: {', '.join(missing)}.")
    out = np.full(shape, np.nan, dtype="float32")
    mask = weights > 0
    out[mask] = weighted[mask] / weights[mask]
    return out


def neighborhood_ratio(mask: np.ndarray, valid: np.ndarray) -> np.ndarray:
    numerator = ndimage.uniform_filter(mask.astype("float32"), size=3, mode="nearest")
    denominator = ndimage.uniform_filter(valid.astype("float32"), size=3, mode="nearest")
    out = np.zeros(mask.shape, dtype="float32")
    ok = denominator > 0
    out[ok] = numerator[ok] / denominator[ok]
    out[~valid] = np.nan
    return out


def pixel_size_meters(transform, crs, bounds) -> tuple[float, float]:
    x_size = abs(transform.a)
    y_size = abs(transform.e)
    if crs and crs.is_projected:
        return x_size, y_size
    center_lat = (bounds.top + bounds.bottom) / 2
    meters_per_degree_lat = 111_320.0
    meters_per_degree_lon = 111_320.0 * math.cos(math.radians(center_lat))
    return x_size * meters_per_degree_lon, y_size * meters_per_degree_lat


def clcd_score(clcd: np.ndarray, valid: np.ndarray, weights: dict[int, float]) -> np.ndarray:
    out = np.full(clcd.shape, np.nan, dtype="float32")
    for code, score in weights.items():
        out[valid & (np.rint(clcd).astype("int16") == code)] = score
    return out


def compute_slope(dem: np.ndarray, valid: np.ndarray, px_m: float, py_m: float) -> tuple[np.ndarray, np.ndarray]:
    filled = dem.copy()
    median = np.nanmedian(filled[valid]) if valid.any() else 0.0
    filled[~valid] = median
    gy, gx = np.gradient(filled, py_m, px_m)
    slope = np.sqrt(gx * gx + gy * gy).astype("float32")
    slope[~valid] = np.nan
    return slope, valid & np.isfinite(slope)


def write_tif(path: Path, data: np.ndarray, template_profile: dict, description: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = np.where(np.isfinite(data), np.clip(data, 0, 1), NODATA).astype("float32")
    profile = template_profile.copy()
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
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(output, 1)
        dst.set_band_description(1, description)


def stats_for(layer: str, data: np.ndarray) -> dict[str, float | int | str]:
    valid = np.isfinite(data)
    values = data[valid]
    total = data.size
    if values.size == 0:
        return {
            "layer": layer,
            "min": math.nan,
            "max": math.nan,
            "mean": math.nan,
            "median": math.nan,
            "p90": math.nan,
            "std": math.nan,
            "valid_count": 0,
            "valid_ratio": 0.0,
        }
    return {
        "layer": layer,
        "min": float(np.nanmin(values)),
        "max": float(np.nanmax(values)),
        "mean": float(np.nanmean(values)),
        "median": float(np.nanmedian(values)),
        "p90": float(np.nanpercentile(values, 90)),
        "std": float(np.nanstd(values)),
        "valid_count": int(values.size),
        "valid_ratio": float(values.size / total),
    }


def save_stats(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["layer", "min", "max", "mean", "median", "p90", "std", "valid_count", "valid_ratio"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def print_stats(rows: list[dict[str, float | int | str]]) -> None:
    print("layer,min,max,mean,median,p90,std,valid_count,valid_ratio")
    for row in rows:
        print(",".join(str(row[field]) for field in ["layer", "min", "max", "mean", "median", "p90", "std", "valid_count", "valid_ratio"]))


def calculate_year(input_dir: Path, year: int, reference: Path | None = None) -> None:
    if year not in FORMAL_YEARS:
        raise ValueError(f"{year} is not a formal four-dimensional year: {FORMAL_YEARS}")

    messages: list[str] = []
    inventory = build_inventory(input_dir, year)
    for key in ["clcd", "dem"]:
        if not inventory[key].path:
            raise RuntimeError(f"{year}: required critical raster missing: {key}")
    for spec in inventory.values():
        if spec.warning:
            log_warning(messages, f"{year}: {spec.warning}")

    template_path = choose_template(inventory, reference)
    out_dir = OUTPUT_ROOT / str(year)

    with rasterio.open(template_path) as template:
        profile = template.profile.copy()
        px_m, py_m = pixel_size_meters(template.transform, template.crs, template.bounds)

        clcd, clcd_valid = read_aligned(inventory["clcd"].path, template, Resampling.nearest)
        clcd_i = np.rint(clcd).astype("int16")
        unique = sorted(int(v) for v in np.unique(clcd_i[clcd_valid]))
        print(f"{year} CLCD unique values: {unique}")
        unknown = [v for v in unique if v not in CLCD_CLASSES]
        if unknown:
            log_warning(messages, f"{year}: CLCD unknown class values: {unknown}")

        dem, dem_valid = read_aligned(inventory["dem"].path, template, Resampling.bilinear)
        dem[~dem_valid] = np.nan

        evi = evi_valid = ndvi = ndvi_valid = None
        if inventory["evi"].path:
            evi, evi_valid = read_aligned(inventory["evi"].path, template, Resampling.bilinear)
            evi, evi_valid = clean_vi(evi, evi_valid, f"{year} EVI", messages)
        if inventory["ndvi"].path:
            ndvi, ndvi_valid = read_aligned(inventory["ndvi"].path, template, Resampling.bilinear)
            ndvi, ndvi_valid = clean_vi(ndvi, ndvi_valid, f"{year} NDVI", messages)

        vi = evi if evi is not None else ndvi
        vi_valid = evi_valid if evi is not None else ndvi_valid
        if vi is None or not vi_valid.any():
            log_warning(messages, f"{year}: EVI/NDVI missing; vegetation patches use CLCD only.")
            vi = np.full(clcd.shape, np.nan, dtype="float32")
            vi_valid = np.zeros(clcd.shape, dtype=bool)

        high_vi = np.zeros(clcd.shape, dtype=bool)
        if vi_valid.any():
            high_vi_threshold = np.nanpercentile(vi[vi_valid], 70)
            high_vi = vi_valid & (vi >= high_vi_threshold)

        land_valid = clcd_valid & np.isin(clcd_i, list(CLCD_CLASSES.keys()))
        ecological_land = np.isin(clcd_i, [2, 4, 5, 9])
        built = clcd_i == 8
        ei = land_valid & (ecological_land | high_vi)
        ei_ratio = neighborhood_ratio(ei, land_valid)
        built_ratio = neighborhood_ratio(land_valid & built, land_valid)
        ers = ei_ratio / (ei_ratio + built_ratio + EPS)
        ers[~land_valid] = np.nan

        ecc = clcd_score(clcd, land_valid, ECC_WEIGHTS)
        hap_parts = []
        for layer, weight, name in [("population", 0.4, "population"), ("gdp", 0.3, "gdp"), ("ntl", 0.3, "nightlight")]:
            spec = inventory[layer]
            if spec.path:
                arr, valid = read_aligned(spec.path, template, Resampling.bilinear)
                arr = np.log1p(np.maximum(arr, 0))
                hap_parts.append((robust_norm(arr, valid, f"{year} {name}", messages), valid, weight, name))
            else:
                hap_parts.append((None, None, weight, name))
        hap = weighted_average(hap_parts, messages, f"{year} HAP")
        erd = ecc / (ecc + hap + EPS)
        erd[~land_valid] = np.nan

        ntl_spec = inventory["ntl"]
        high_ntl = np.zeros(clcd.shape, dtype=bool)
        if ntl_spec.path:
            ntl_raw, ntl_valid = read_aligned(ntl_spec.path, template, Resampling.bilinear)
            if ntl_valid.any():
                ntl_thr = np.nanpercentile(ntl_raw[ntl_valid], 80)
                high_ntl = ntl_valid & (ntl_raw >= ntl_thr)
        else:
            log_warning(messages, f"{year}: nightlight missing; ERM source uses built-up only.")
        source = land_valid & (built | high_ntl)
        sink = land_valid & (np.isin(clcd_i, [2, 5, 9]) | high_vi)
        if not sink.any():
            log_warning(messages, f"{year}: no sink pixels; ERM set to 0.")
            erm = np.zeros(clcd.shape, dtype="float32")
            erm[~land_valid] = np.nan
        else:
            sampling = (py_m, px_m)
            distance_to_sink = ndimage.distance_transform_edt(~sink, sampling=sampling).astype("float32")
            erm = np.exp(-distance_to_sink / 1000.0).astype("float32")
            erm[sink] = 1.0
            erm[~land_valid] = np.nan
        erm_med = np.nanmedian(erm)
        erm_p90 = np.nanpercentile(erm[np.isfinite(erm)], 90) if np.isfinite(erm).any() else np.nan
        if np.isclose(erm_med, 1.0) and np.isclose(erm_p90, 1.0):
            log_warning(messages, f"{year}: ERM appears saturated (median=1, p90=1).")

        relative_dem = dem - np.nanmin(dem[dem_valid])
        relative_dem_risk = robust_norm(relative_dem, dem_valid, f"{year} relative DEM", messages, invert=True)
        slope, slope_valid = compute_slope(dem, dem_valid, px_m, py_m)
        slope_risk = robust_norm(slope, slope_valid, f"{year} slope", messages, invert=True)

        water_risk = np.full(clcd.shape, np.nan, dtype="float32")
        water_spec = inventory["water"]
        if water_spec.path:
            is_frequency = any(k in tokenize(water_spec.path) for k in ["frequency", "occurrence"])
            water_resampling = Resampling.bilinear if is_frequency else Resampling.nearest
            water, water_valid = read_aligned(water_spec.path, template, water_resampling)
            if is_frequency:
                occurrence = water.astype("float32")
                if water_valid.any() and np.nanmax(occurrence[water_valid]) > 1:
                    occurrence[water_valid] /= 100.0
                permanent = water_valid & (occurrence >= 0.99)
                wr_valid = water_valid & ~permanent
                water_risk = robust_norm(occurrence, wr_valid, f"{year} water occurrence", messages)
                water_risk[land_valid & ~wr_valid] = 0.0
                water_risk[permanent] = 0.0
            else:
                log_warning(messages, f"{year}: no water occurrence; using water class proximity surrogate.")
                water_class = np.rint(water).astype("int16")
                water_mask = water_valid & np.isin(water_class, [2, 3])
                if water_mask.any():
                    dist_water = ndimage.distance_transform_edt(~water_mask, sampling=(py_m, px_m)).astype("float32")
                    water_risk = np.exp(-dist_water / 1000.0).astype("float32")
                    water_risk[water_mask] = 0.0
                    water_risk[~water_valid] = np.nan
                else:
                    log_warning(messages, f"{year}: water class has no water pixels; water risk set to 0.")
                    water_risk = np.zeros(clcd.shape, dtype="float32")
        else:
            log_warning(messages, f"{year}: water missing; water risk set to 0.")
            water_risk = np.zeros(clcd.shape, dtype="float32")

        land_risk = clcd_score(clcd, land_valid, LAND_RISK_WEIGHTS)
        fri = 0.30 * relative_dem_risk + 0.20 * slope_risk + 0.30 * water_risk + 0.20 * land_risk
        fri[~land_valid] = np.nan
        fri = np.clip(fri, 0, 1)
        erf = 1.0 - fri
        erf[~np.isfinite(fri)] = np.nan

        er_raw = 0.25 * ers + 0.25 * erd + 0.25 * erm + 0.25 * erf
        if vi_valid.any():
            vi_mean = np.nanmean(vi[vi_valid])
            vegetation_factor = np.clip(vi / vi_mean, 0.7, 1.3) if vi_mean and np.isfinite(vi_mean) else 1.0
        else:
            vegetation_factor = 1.0
        er = robust_norm(er_raw * vegetation_factor, np.isfinite(er_raw), f"{year} ER", messages)
        er[~land_valid] = np.nan

        outputs = {
            "er": (er, "Four-dimensional ecological resilience ER, 0-1"),
            "ers": (ers, "Scale resilience ERS, 0-1"),
            "erd": (erd, "Density resilience ERD, 0-1"),
            "erm": (erm, "Morphology resilience ERM, 0-1"),
            "erf": (erf, "Flood resilience ERF, 0-1"),
            "fri": (fri, "Flood risk FRI, 0-1"),
        }
        for name, (arr, desc) in outputs.items():
            write_tif(out_dir / f"{name}_{year}.tif", arr, profile, desc)

    rows = [stats_for(name, arr) for name, (arr, _) in outputs.items()]
    save_stats(out_dir / f"manual_resilience_stats_{year}.csv", rows)
    if messages:
        (out_dir / f"manual_resilience_warnings_{year}.txt").write_text("\n".join(messages), encoding="utf-8")
    print_stats(rows)
    print(f"wrote {out_dir}")


def main() -> None:
    args = parse_args()
    for year in args.years:
        calculate_year(args.input, year, args.reference)


if __name__ == "__main__":
    main()
