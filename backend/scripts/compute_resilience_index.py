from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[2]
ALIGNED_DIR = ROOT / "data" / "processed" / "aligned"
INDEX_DIR = ROOT / "data" / "processed" / "indices"

NODATA = -9999.0


INPUTS = {
    "ndvi_2000": ALIGNED_DIR / "ndvi_2000_epsg4326_250m.tif",
    "ndvi_2025": ALIGNED_DIR / "ndvi_2025_epsg4326_250m.tif",
    "evi_2000": ALIGNED_DIR / "evi_2000_epsg4326_250m.tif",
    "evi_2025": ALIGNED_DIR / "evi_2025_epsg4326_250m.tif",
    "clcd_2025": ALIGNED_DIR / "clcd_2025_epsg4326_250m.tif",
    "water_frequency": ALIGNED_DIR / "water_frequency_2000_2021_epsg4326_250m.tif",
    "gdp_2023": ALIGNED_DIR / "gdp_2023_epsg4326_250m.tif",
    "population_2024": ALIGNED_DIR / "population_2024_epsg4326_250m.tif",
    "ntl_2024": ALIGNED_DIR / "ntl_2024_epsg4326_250m.tif",
}


def read_band(path: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        nodata = src.nodata
        valid = np.isfinite(arr)
        if nodata is not None:
            valid &= arr != nodata
        return arr, valid, src.profile.copy()


def normalize(arr: np.ndarray, valid: np.ndarray, invert: bool = False) -> np.ndarray:
    out = np.full(arr.shape, np.nan, dtype="float32")
    if not valid.any():
        return out
    values = arr[valid].astype("float64")
    low, high = np.nanpercentile(values, [2, 98])
    if high <= low:
        out[valid] = 0.5
        return out
    scaled = (arr[valid] - low) / (high - low)
    scaled = np.clip(scaled, 0, 1)
    if invert:
        scaled = 1 - scaled
    out[valid] = scaled.astype("float32")
    return out


def normalize_delta(current: np.ndarray, baseline: np.ndarray, valid: np.ndarray) -> np.ndarray:
    delta = np.full(current.shape, np.nan, dtype="float32")
    delta[valid] = current[valid] - baseline[valid]
    return normalize(delta, valid)


def clcd_ecological_score(clcd: np.ndarray, valid: np.ndarray) -> np.ndarray:
    score = np.full(clcd.shape, np.nan, dtype="float32")
    score[valid] = 0.35
    score[np.isin(clcd, [2, 3, 4])] = 0.95
    score[clcd == 5] = 0.85
    score[clcd == 1] = 0.62
    score[np.isin(clcd, [6, 7, 9])] = 0.45
    score[clcd == 8] = 0.12
    return score


def nanmean_stack(arrays: list[np.ndarray]) -> np.ndarray:
    stack = np.stack(arrays)
    valid_count = np.sum(np.isfinite(stack), axis=0)
    total = np.nansum(stack, axis=0)
    out = np.full(arrays[0].shape, np.nan, dtype="float32")
    mask = valid_count > 0
    out[mask] = (total[mask] / valid_count[mask]).astype("float32")
    return out


def write_index(path: Path, data: np.ndarray, profile: dict, description: str) -> None:
    output = np.where(np.isfinite(data), data, NODATA).astype("float32")
    out_profile = profile.copy()
    out_profile.update(
        {
            "driver": "GTiff",
            "count": 1,
            "dtype": "float32",
            "nodata": NODATA,
            "compress": "deflate",
            "predictor": 2,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "BIGTIFF": "IF_SAFER",
        }
    )
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(output, 1)
        dst.set_band_description(1, description)


def stats(name: str, data: np.ndarray) -> str:
    valid = data[np.isfinite(data)]
    q = np.nanpercentile(valid, [0, 50, 90, 100])
    return (
        f"{name}: valid={valid.size}, "
        f"min={q[0]:.4f}, median={q[1]:.4f}, p90={q[2]:.4f}, max={q[3]:.4f}"
    )


def main() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    ndvi_2000, ndvi_2000_valid, profile = read_band(INPUTS["ndvi_2000"])
    ndvi_2025, ndvi_2025_valid, _ = read_band(INPUTS["ndvi_2025"])
    evi_2000, evi_2000_valid, _ = read_band(INPUTS["evi_2000"])
    evi_2025, evi_2025_valid, _ = read_band(INPUTS["evi_2025"])
    clcd, clcd_valid, _ = read_band(INPUTS["clcd_2025"])
    water_frequency, water_valid, _ = read_band(INPUTS["water_frequency"])
    gdp, gdp_valid, _ = read_band(INPUTS["gdp_2023"])
    population, pop_valid, _ = read_band(INPUTS["population_2024"])
    ntl, ntl_valid, _ = read_band(INPUTS["ntl_2024"])

    base_valid = ndvi_2025_valid | evi_2025_valid | clcd_valid

    resistance = nanmean_stack(
        [
            normalize(ndvi_2025, ndvi_2025_valid),
            normalize(evi_2025, evi_2025_valid),
            normalize(water_frequency, water_valid),
            clcd_ecological_score(clcd, clcd_valid),
        ]
    )

    recovery_valid = ndvi_2000_valid & ndvi_2025_valid & evi_2000_valid & evi_2025_valid
    recovery = nanmean_stack(
        [
            normalize_delta(ndvi_2025, ndvi_2000, recovery_valid),
            normalize_delta(evi_2025, evi_2000, recovery_valid),
        ]
    )

    adaptation = nanmean_stack(
        [
            normalize(np.log1p(np.maximum(gdp, 0)), gdp_valid),
            normalize(np.log1p(np.maximum(population, 0)), pop_valid),
            normalize(np.log1p(np.maximum(ntl, 0)), ntl_valid, invert=True),
        ]
    )

    resilience = nanmean_stack([resistance, recovery, adaptation])
    resilience[~base_valid] = np.nan

    outputs = {
        "resistance_2025.tif": (resistance, "MVP resistance component, 0-1"),
        "recovery_2025.tif": (recovery, "MVP recovery component, 0-1"),
        "adaptation_2025.tif": (adaptation, "MVP adaptation component, 0-1"),
        "resilience_index_2025.tif": (resilience, "MVP ecological resilience index, 0-1"),
    }

    for filename, (data, description) in outputs.items():
        write_index(INDEX_DIR / filename, data, profile, description)
        print(stats(filename, data))

    print(f"wrote {INDEX_DIR}")


if __name__ == "__main__":
    main()
