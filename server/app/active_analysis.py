from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Any

from .config import get_settings
from .context import detect_analysis_years, detect_layers, is_regional_extreme_question, layer_label, timeline_stat


def _project_root() -> Path:
    return get_settings().data_path.parent.parent


def _query_grid_candidates(layer_id: str, year: int | str) -> list[Path]:
    root = _project_root()
    return [
        root / "frontend" / "data" / "query_grids" / f"{layer_id}_{year}.json",
        root / "frontend" / "data" / "query_grids" / "four_dim" / f"{layer_id}_{year}.json",
    ]


@lru_cache(maxsize=128)
def _load_query_grid(layer_id: str, year: int) -> dict[str, Any] | None:
    for path in _query_grid_candidates(layer_id, year):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and math.isfinite(float(value))


def _cell_center(bounds: dict[str, Any], width: int, height: int, row: int, col: int) -> tuple[float, float] | None:
    try:
        west = float(bounds["west"])
        east = float(bounds["east"])
        south = float(bounds["south"])
        north = float(bounds["north"])
    except (KeyError, TypeError, ValueError):
        return None
    lon = west + (col + 0.5) * (east - west) / width
    lat = north - (row + 0.5) * (north - south) / height
    return lon, lat


def compute_grid_summary(layer_id: str, year: int) -> dict[str, Any] | None:
    grid = _load_query_grid(layer_id, year)
    if not grid:
        return None

    values = grid.get("values")
    width = int(grid.get("width") or 0)
    height = int(grid.get("height") or 0)
    if not isinstance(values, list) or width <= 0 or height <= 0:
        return None

    valid: list[float] = []
    max_item: tuple[float, int, int] | None = None
    min_item: tuple[float, int, int] | None = None
    for row_idx, row in enumerate(values):
        if not isinstance(row, list):
            continue
        for col_idx, raw in enumerate(row):
            if not _is_number(raw):
                continue
            value = float(raw)
            valid.append(value)
            if max_item is None or value > max_item[0]:
                max_item = (value, row_idx, col_idx)
            if min_item is None or value < min_item[0]:
                min_item = (value, row_idx, col_idx)

    if not valid:
        return None

    bounds = grid.get("bounds") if isinstance(grid.get("bounds"), dict) else {}
    max_location = _cell_center(bounds, width, height, max_item[1], max_item[2]) if max_item else None
    min_location = _cell_center(bounds, width, height, min_item[1], min_item[2]) if min_item else None
    valid_count = len(valid)
    total_count = width * height

    return {
        "layer": layer_id,
        "layer_label": layer_label(layer_id),
        "year": year,
        "width": width,
        "height": height,
        "valid_count": valid_count,
        "total_count": total_count,
        "valid_ratio": valid_count / total_count if total_count else None,
        "computed_mean": sum(valid) / valid_count,
        "computed_median": median(valid),
        "computed_min": min_item[0] if min_item else None,
        "computed_max": max_item[0] if max_item else None,
        "max_row_col": [max_item[1], max_item[2]] if max_item else None,
        "min_row_col": [min_item[1], min_item[2]] if min_item else None,
        "max_lon_lat": list(max_location) if max_location else None,
        "min_lon_lat": list(min_location) if min_location else None,
    }


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "暂无"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def build_active_analysis_context(query: str, year: int | None = None, layer: str | None = None) -> str:
    years = detect_analysis_years(query, year)
    layers = detect_layers(query, layer)
    if not years or not layers:
        return ""

    summaries = []
    for target_year in years[:3]:
        for target_layer in layers[:4]:
            summary = compute_grid_summary(target_layer, target_year)
            if summary:
                summaries.append(summary)

    lines = ["\n[主动计算分析结果：必须优先使用，不得忽略]"]
    if not summaries:
        lines.append("已完成 RAG 检索，但当前问题对应图层/年份没有可直接读取的 query grid，因此无法进行栅格级派生计算。")
        return "\n".join(lines)

    lines.append("计算流程：先用 RAG 定位年份和图层，再读取前端可查询栅格矩阵，剔除空值后计算抽样网格均值、中位数、极值、有效像元比例和极值像元位置。注意：该位置只对应可查询网格抽样结果；完整栅格统计配置中的极值可用于数值核验，但没有对应坐标时不能把抽样坐标绑定到完整栅格极值。")
    for item in summaries:
        max_lon_lat = item.get("max_lon_lat")
        min_lon_lat = item.get("min_lon_lat")
        max_location = f"约 经度{_fmt(max_lon_lat[0], 5)}、纬度{_fmt(max_lon_lat[1], 5)}" if max_lon_lat else "暂无坐标"
        min_location = f"约 经度{_fmt(min_lon_lat[0], 5)}、纬度{_fmt(min_lon_lat[1], 5)}" if min_lon_lat else "暂无坐标"
        lines.append(
            f"- {item['year']} 年 {item['layer_label']}（{item['layer']}）："
            f"抽样有效像元 {item['valid_count']}/{item['total_count']}，"
            f"抽样有效比例 {_fmt((item.get('valid_ratio') or 0) * 100, 2)}%；"
            f"抽样计算均值 {_fmt(item.get('computed_mean'))}，抽样中位数 {_fmt(item.get('computed_median'))}，"
            f"抽样最小值 {_fmt(item.get('computed_min'))}（{min_location}），"
            f"抽样最大值 {_fmt(item.get('computed_max'))}（{max_location}）。"
        )
        stat = timeline_stat(item["year"], item["layer"])
        if isinstance(stat, dict):
            lines.append(
                f"  与 RAG 统计配置交叉核验：median={stat.get('median')}，min={stat.get('min')}，max={stat.get('max')}，p90={stat.get('p90')}。"
            )

    if is_regional_extreme_question(query):
        lines.append(
            "可计算性判断：现有栅格可以主动计算研究区整体统计、最高/最低像元及其空间位置；"
            "但‘哪个县平均最高’需要县域边界与分区聚合。当前没有县域分区统计时，不能把最高像元或全区最大值等同于县平均最高。"
            "如果用户需要县名，应先生成县域 zonal statistics，再按县级均值排序。"
        )

    lines.append("回答时请必须输出抽样计算出的均值、中位数、最大值、最大值位置，并以‘RAG检索—可计算性判断—主动计算—结论/建议’的结构输出；同时说明抽样结果与完整统计配置的区别，不要暴露本地文件路径。")
    return "\n".join(lines)
