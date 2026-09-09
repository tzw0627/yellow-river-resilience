from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean


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

# The station table lists 54910 as Liangshan. Keep it explicit here rather than
# relying on a spreadsheet reader at build time.
STATION_NAMES["54910"] = ("梁山", "山东")


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


def load_history(directory: Path) -> tuple[dict[str, list[float]], dict[str, set[int]]]:
    values: dict[str, list[float]] = defaultdict(list)
    years: dict[str, set[int]] = defaultdict(set)
    for path in directory.glob("Pre*.txt"):
        with path.open(errors="ignore") as source:
            for line in source:
                fields = line.split()
                if len(fields) < 10 or fields[0] not in STATION_NAMES:
                    continue
                try:
                    amount = legacy_precipitation(fields[9])
                    year = int(fields[4])
                except ValueError:
                    continue
                if amount is None:
                    continue
                years[fields[0]].add(year)
                if amount > 0:
                    values[fields[0]].append(amount)
    return values, years


def load_2020(directory: Path) -> tuple[dict[str, dict[date, float]], dict[str, tuple[float, float, float]]]:
    series: dict[str, dict[date, float]] = defaultdict(dict)
    coordinates: dict[str, tuple[float, float, float]] = {}
    for path in sorted(directory.glob("Pre2020*.txt")):
        month = int(path.stem[-2:])
        modern = month >= 4
        with path.open(errors="ignore") as source:
            for line in source:
                fields = line.split()
                if len(fields) < 10 or fields[0] not in STATION_NAMES:
                    continue
                try:
                    lat = float(fields[1]) if modern else degree_minute(fields[1])
                    lon = float(fields[2]) if modern else degree_minute(fields[2])
                    elevation = float(fields[3]) if modern else int(fields[3]) / 10
                    observed = date(int(fields[4]), int(fields[5]), int(fields[6]))
                    amount = float(fields[9]) if modern else legacy_precipitation(fields[9])
                except ValueError:
                    continue
                if amount is None or amount >= 9999:
                    continue
                series[fields[0]][observed] = round(amount, 2)
                coordinates[fields[0]] = (lat, lon, elevation)
    return series, coordinates


def build_payload(source_root: Path) -> dict:
    history_dir = source_root / "2020黄河流域气象数据" / "data" / "PRE"
    current_dir = source_root / "PRE"
    history, station_years = load_history(history_dir)
    series, coordinates = load_2020(current_dir)
    pooled_history = [value for values in history.values() for value in values]

    stations = []
    for station_id in sorted(series):
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

    all_dates = sorted({observed for values in series.values() for observed in values})
    days = []
    for observed in all_dates:
        observations = []
        for station in stations:
            station_id = station["id"]
            amount = series[station_id].get(observed)
            if amount is None:
                continue
            rolling_values = [series[station_id].get(observed - timedelta(days=offset)) for offset in (2, 1, 0)]
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
                "date": observed.isoformat(),
                "peak": round(peak, 1),
                "max3Day": round(max(rolling, default=0), 1),
                "mean": round(mean(rainfall), 1) if rainfall else 0,
                "rainstormStations": sum(1 for value in rainfall if value >= 50),
                "affectedStations": sum(1 for value in rainfall if value >= 10),
                "level": rain_level(peak),
                "observations": observations,
            }
        )

    ranked = sorted(days, key=lambda item: (item["peak"] + item["rainstormStations"] * 16 + item["mean"] * 2), reverse=True)
    selected = []
    for item in ranked:
        current = date.fromisoformat(item["date"])
        if any(abs((current - date.fromisoformat(other["date"])).days) <= 2 for other in selected):
            continue
        if item["peak"] < 50:
            continue
        selected.append(item)
        if len(selected) == 8:
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
            "observationYear": 2020,
            "historyRange": "1954—2019（研究区长期站）",
            "temporalResolution": "逐日；含20—08时、08—20时和20—20时累计字段",
            "stationCount": len(stations),
            "longTermStationCount": sum(1 for station in stations if station["historyStart"] is not None),
            "scope": "研究区边界内及沿线邻近站点",
            "usage": "真实历史事件复盘、极端程度判断与洪水风险联动研判",
            "limitation": "数据最新至2020年且以日尺度为主，不代表实时预警。",
        },
        "stations": stations,
        "events": events,
        "days": days,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="构建实测降水应急研判前端数据")
    parser.add_argument("source_root", type=Path, help="气象数据根目录")
    parser.add_argument("output", type=Path, help="输出 JSON 路径")
    args = parser.parse_args()
    payload = build_payload(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {args.output} ({len(payload['stations'])} stations, {len(payload['days'])} days, {len(payload['events'])} events)")


if __name__ == "__main__":
    main()
