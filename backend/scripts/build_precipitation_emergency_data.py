from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean


START_YEAR = 2000
END_YEAR = 2020
EVENTS_PER_YEAR = 8

STATION_NAMES = {
    "53983": ("封丘", "河南"),
    "53987": ("武陟", "河南"),
    "53989": ("原阳", "河南"),
    "53998": ("长垣", "河南"),
    "54817": ("台前", "河南"),
    "54900": ("濮阳", "河南"),
    "54903": ("范县", "河南"),
    "54904": ("鄄城", "山东"),
    "54908": ("东明", "山东"),
    "54910": ("梁山", "山东"),
    "54911": ("东平", "山东"),
    "57071": ("孟津", "河南"),
    "57072": ("孟州", "河南"),
    "57079": ("温县", "河南"),
    "57080": ("巩义", "河南"),
    "57081": ("荥阳", "河南"),
    "57090": ("中牟", "河南"),
    "57091": ("开封", "河南"),
    "57093": ("兰考", "河南"),
}


def degree_minute(value: str) -> float:
    raw = int(value)
    return raw // 100 + (raw % 100) / 60


def legacy_precipitation(value: str) -> float | None:
    raw = int(value)
    if raw in {32766, 999990, 999999}:
        return None
    if raw == 32700:
        return 0.05
    if 30000 <= raw < 33000:
        return (raw % 1000) / 10
    return raw / 10


def quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def percentile(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    return sum(1 for item in values if item <= value) / len(values)


def rain_level(value: float) -> str:
    if value >= 250:
        return "特大暴雨"
    if value >= 100:
        return "大暴雨"
    if value >= 50:
        return "暴雨"
    if value >= 25:
        return "大雨"
    if value >= 10:
        return "中雨"
    if value > 0:
        return "小雨"
    return "无降水"


def load_legacy_data(
    directory: Path,
) -> tuple[
    dict[str, dict[date, float]],
    dict[str, list[float]],
    dict[str, set[int]],
    dict[str, tuple[float, float, float]],
]:
    series: dict[str, dict[date, float]] = defaultdict(dict)
    history: dict[str, list[float]] = defaultdict(list)
    years: dict[str, set[int]] = defaultdict(set)
    coordinates: dict[str, tuple[float, float, float]] = {}

    for path in sorted(directory.glob("Pre*.txt")):
        with path.open(errors="ignore") as source:
            for line in source:
                fields = line.split()
                station_id = fields[0] if fields else ""
                if len(fields) < 10 or station_id not in STATION_NAMES:
                    continue
                try:
                    observed = date(int(fields[4]), int(fields[5]), int(fields[6]))
                    amount = legacy_precipitation(fields[9])
                    coordinates[station_id] = (
                        degree_minute(fields[1]),
                        degree_minute(fields[2]),
                        int(fields[3]) / 10,
                    )
                except (ValueError, OverflowError):
                    continue
                if amount is None:
                    continue
                years[station_id].add(observed.year)
                if amount > 0:
                    history[station_id].append(amount)
                if START_YEAR <= observed.year < END_YEAR:
                    series[station_id][observed] = round(amount, 2)

    return series, history, years, coordinates


def add_2020_data(
    directory: Path,
    series: dict[str, dict[date, float]],
    coordinates: dict[str, tuple[float, float, float]],
) -> None:
    for path in sorted(directory.glob("Pre2020*.txt")):
        month = int(path.stem[-2:])
        modern = month >= 4
        with path.open(errors="ignore") as source:
            for line in source:
                fields = line.split()
                station_id = fields[0] if fields else ""
                if len(fields) < 10 or station_id not in STATION_NAMES:
                    continue
                try:
                    lat = float(fields[1]) if modern else degree_minute(fields[1])
                    lon = float(fields[2]) if modern else degree_minute(fields[2])
                    elevation = float(fields[3]) if modern else int(fields[3]) / 10
                    observed = date(int(fields[4]), int(fields[5]), int(fields[6]))
                    amount = float(fields[9]) if modern else legacy_precipitation(fields[9])
                except (ValueError, OverflowError):
                    continue
                if amount is None or amount >= 9999:
                    continue
                series[station_id][observed] = round(amount, 2)
                coordinates[station_id] = (lat, lon, elevation)


def build_stations(
    series: dict[str, dict[date, float]],
    history: dict[str, list[float]],
    station_years: dict[str, set[int]],
    coordinates: dict[str, tuple[float, float, float]],
) -> list[dict]:
    pooled_history = [value for values in history.values() for value in values]
    stations = []
    for station_id in sorted(STATION_NAMES):
        if station_id not in coordinates or station_id not in series:
            continue
        lat, lon, elevation = coordinates[station_id]
        name, province = STATION_NAMES[station_id]
        station_history = history.get(station_id) or pooled_history
        years = station_years.get(station_id, set())
        stations.append(
            {
                "id": station_id,
                "name": name,
                "province": province,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "elevation": round(elevation, 1),
                "historyStart": min(years) if years else None,
                "historyEnd": max(years) if years else None,
                "wetDayP95": round(quantile(station_history, 0.95), 1),
                "wetDayP99": round(quantile(station_history, 0.99), 1),
            }
        )
    return stations


def build_year_payload(
    year: int,
    stations: list[dict],
    series: dict[str, dict[date, float]],
    history: dict[str, list[float]],
) -> dict:
    pooled_history = [value for values in history.values() for value in values]
    year_stations = [
        station
        for station in stations
        if any(observed.year == year for observed in series[station["id"]])
    ]
    cursor = date(year, 1, 1)
    end = date(year, 12, 31)
    days = []

    while cursor <= end:
        observations = []
        for station in year_stations:
            station_id = station["id"]
            amount = series[station_id].get(cursor)
            if amount is None:
                continue
            rolling_values = [series[station_id].get(cursor - timedelta(days=offset)) for offset in (2, 1, 0)]
            rolling3 = sum(value for value in rolling_values if value is not None)
            station_history = history.get(station_id) or pooled_history
            observations.append(
                {
                    "stationId": station_id,
                    "rainfall": round(amount, 1),
                    "rolling3": round(rolling3, 1),
                    "percentile": round(percentile(station_history, amount) * 100, 1) if amount > 0 else 0,
                    "level": rain_level(amount),
                }
            )
        rainfall = [item["rainfall"] for item in observations]
        rolling = [item["rolling3"] for item in observations]
        peak = max(rainfall, default=0)
        days.append(
            {
                "date": cursor.isoformat(),
                "peak": round(peak, 1),
                "max3Day": round(max(rolling, default=0), 1),
                "mean": round(mean(rainfall), 1) if rainfall else 0,
                "rainstormStations": sum(1 for value in rainfall if value >= 50),
                "affectedStations": sum(1 for value in rainfall if value >= 10),
                "level": rain_level(peak),
                "observations": observations,
            }
        )
        cursor += timedelta(days=1)

    ranked = sorted(days, key=lambda item: (item["peak"] + item["rainstormStations"] * 16 + item["mean"] * 2), reverse=True)
    selected = []
    for item in ranked:
        current = date.fromisoformat(item["date"])
        if item["peak"] < 50:
            continue
        if any(abs((current - date.fromisoformat(other["date"])).days) <= 2 for other in selected):
            continue
        selected.append(item)
        if len(selected) == EVENTS_PER_YEAR:
            break

    events = [
        {
            "id": f"observed-{item['date']}",
            "date": item["date"],
            "label": f"{item['date']} {item['level']}过程",
            "source": "国家级地面气象站逐日实测",
            "peak": item["peak"],
            "max3Day": item["max3Day"],
            "rainstormStations": item["rainstormStations"],
        }
        for item in selected
    ]

    return {
        "metadata": {
            "title": "黄河中下游滩区实测降水应急研判数据",
            "source": "中国地面气候资料日值数据集（用户提供本地文件）",
            "observationYear": year,
            "historyRange": "1951—2019（研究区长期站）",
            "temporalResolution": "逐日；采用20—20时累计降水量",
            "stationCount": len(year_stations),
            "longTermStationCount": sum(1 for station in year_stations if station["historyStart"] is not None),
            "scope": "研究区边界内及沿线邻近站点",
            "usage": "真实历史事件复盘、极端程度判断与洪水风险联动研判",
            "limitation": "数据覆盖2000—2020年且以日尺度为主，不代表实时预警。",
        },
        "stations": year_stations,
        "events": events,
        "days": days,
    }


def build_files(source_root: Path, output_directory: Path) -> None:
    history_dir = source_root / "2020黄河流域气象数据" / "data" / "PRE"
    current_dir = source_root / "PRE"
    series, history, station_years, coordinates = load_legacy_data(history_dir)
    add_2020_data(current_dir, series, coordinates)
    stations = build_stations(series, history, station_years, coordinates)
    output_directory.mkdir(parents=True, exist_ok=True)

    catalog_years = []
    for year in range(START_YEAR, END_YEAR + 1):
        payload = build_year_payload(year, stations, series, history)
        filename = f"precipitation_{year}.json"
        output_path = output_directory / filename
        output_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        strongest = payload["events"][0] if payload["events"] else None
        catalog_years.append(
            {
                "year": year,
                "file": filename,
                "dayCount": len(payload["days"]),
                "stationCount": len(payload["stations"]),
                "eventCount": len(payload["events"]),
                "peak": strongest["peak"] if strongest else 0,
                "peakDate": strongest["date"] if strongest else None,
            }
        )
        print(f"wrote {output_path} ({len(payload['days'])} days, {len(payload['events'])} events)")

    catalog = {
        "metadata": {
            "title": "黄河中下游滩区2000—2020年逐日降水目录",
            "source": "中国地面气候资料日值数据集（用户提供本地文件）",
            "startYear": START_YEAR,
            "endYear": END_YEAR,
            "temporalResolution": "逐日",
            "stationCount": len(stations),
        },
        "years": catalog_years,
    }
    catalog_path = output_directory / "index.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {catalog_path} ({len(catalog_years)} years)")


def main() -> None:
    parser = argparse.ArgumentParser(description="构建2000—2020年实测降水应急研判前端数据")
    parser.add_argument("source_root", type=Path, help="气象数据根目录")
    parser.add_argument("output_directory", type=Path, help="输出目录")
    args = parser.parse_args()
    build_files(args.source_root, args.output_directory)


if __name__ == "__main__":
    main()
