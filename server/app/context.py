from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import get_settings


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def load_summary() -> dict[str, Any]:
    return _read_json(get_settings().data_path / "layer_summary.json")


@lru_cache
def load_supplemental_stats() -> dict[str, Any]:
    """读取前端生成的普通图层统计，补充 NDVI/EVI/CLCD/GDP 等数据。"""
    data_path = get_settings().data_path
    project_root = data_path.parent.parent
    generated_dir = project_root / "web" / "src" / "config" / "generated"
    merged: dict[str, Any] = {}
    for name in ["layerStatsAligned.ts", "layerStats2024.ts"]:
        path = generated_dir / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        match = re.search(r"export const \w+ = (\{.*\})\s*;", text, re.S)
        if not match:
            continue
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        for year, layers in payload.items():
            if isinstance(layers, dict):
                merged.setdefault(str(year), {}).update(layers)
    return merged


@lru_cache
def load_twin() -> dict[str, Any]:
    return _read_json(get_settings().data_path / "twin_model.json")


def layer_label(layer_id: str) -> str:
    for layer in load_summary().get("layers", []):
        if layer.get("id") == layer_id:
            return layer.get("label", layer_id)
    return layer_id


def timeline_stat(year: int | str, layer_id: str) -> dict[str, Any] | None:
    year_key = str(year)
    summary_stat = load_summary().get("timeline", {}).get(year_key, {}).get(layer_id)
    supplemental_stat = load_supplemental_stats().get(year_key, {}).get(layer_id)
    if isinstance(summary_stat, dict) and isinstance(supplemental_stat, dict):
        return {**supplemental_stat, **summary_stat}
    return summary_stat or supplemental_stat


LAYER_ALIASES: dict[str, list[str]] = {
    "ndvi": ["ndvi", "植被指数", "归一化植被"],
    "evi": ["evi", "增强型植被"],
    "clcd": ["clcd", "土地利用", "土地覆盖", "land use", "land cover"],
    "water": ["water", "水体", "水域", "水系"],
    "ntl": ["ntl", "夜间灯光", "灯光", "night light", "nighttime"],
    "gdp": ["gdp", "经济", "生产总值"],
    "landscan": ["landscan", "population", "人口"],
    "terraclimate": ["terraclimate", "气候", "水文气候"],
    "ri": ["ri", "resilience index", "生态韧性指数", "综合韧性指数"],
    "four_dim_er": ["four_dim_er", "四维综合", "综合生态韧性", "综合韧性", "er"],
    "four_dim_ers": ["four_dim_ers", "规模韧性", "ers"],
    "four_dim_erd": ["four_dim_erd", "密度韧性", "erd"],
    "four_dim_erm": ["four_dim_erm", "形态韧性", "erm"],
    "four_dim_erf": ["four_dim_erf", "洪水韧性", "erf"],
    "four_dim_fri": ["four_dim_fri", "洪水风险", "fri", "风险"],
}

METRIC_ALIASES: dict[str, list[str]] = {
    "median": ["中位数", "median", "中值"],
    "mean": ["平均", "均值", "mean", "average"],
    "min": ["最小", "最低", "min"],
    "max": ["最大", "最高", "max"],
    "p90": ["p90", "90分位", "90 分位", "百分之90", "90%"],
    "validRatio": ["有效比例", "有效像元比例", "validratio", "valid ratio"],
}


def is_method_question(text: str) -> bool:
    lowered = text.lower()
    keywords = [
        "如何计算", "怎么计算", "怎么算", "如何得到", "怎么得到", "用什么方法", "哪些方法", "计算方法", "方法", "原理", "流程", "指标体系", "权重", "公式",
        "how", "method", "calculate", "computed", "formula", "workflow", "principle",
    ]
    return any(keyword in lowered for keyword in keywords)


def is_regional_extreme_question(text: str) -> bool:
    lowered = text.lower()
    region_terms = ["哪个", "哪里", "哪儿", "县", "区县", "区域", "地区", "位置", "county", "region", "area", "where"]
    extreme_terms = ["最高", "最低", "最大", "最小", "平均最高", "平均最低", "top", "highest", "lowest", "maximum", "minimum"]
    return any(term in lowered for term in region_terms) and any(term in lowered for term in extreme_terms)


def detect_years(text: str) -> list[int]:
    years = [int(item) for item in re.findall(r"(?:19|20)\d{2}", text)]
    available = {int(y) for y in load_summary().get("years", [])}
    available.update(int(y) for y in load_supplemental_stats().keys() if str(y).isdigit())
    return [year for year in years if year in available]


def detect_analysis_years(text: str, fallback_year: int | None = None) -> list[int]:
    explicit = detect_years(text)
    available = _available_years()
    if len(explicit) >= 2 and re.search(r"到|至|-|~|—|--|from|\bto\b", text.lower()):
        start, end = min(explicit), max(explicit)
        return [year for year in available if start <= year <= end]
    if explicit:
        return explicit
    return [fallback_year] if fallback_year else available[-2:]


def detect_layers(text: str, fallback_layer: str | None = None) -> list[str]:
    lowered = text.lower()
    layers: list[str] = []
    for layer_id, aliases in LAYER_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            layers.append(layer_id)
    if not layers and fallback_layer:
        layers.append(fallback_layer)
    return list(dict.fromkeys(layers))


def detect_metrics(text: str) -> list[str]:
    lowered = text.lower()
    metrics: list[str] = []
    for metric, aliases in METRIC_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            metrics.append(metric)
    return metrics


def _format_value(metric: str, value: Any) -> str:
    if value is None:
        return "暂无数据"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if metric == "validRatio":
        return f"{number * 100:.2f}%"
    return f"{number:.4f}"


def _local_stat_source(layer_id: str, year: int | str, stat: dict[str, Any]) -> str:
    data_path = get_settings().data_path
    project_root = data_path.parent.parent
    candidates = [
        project_root / "data" / "processed" / "aligned" / f"{layer_id}_{year}_epsg4326_250m.tif",
        project_root / "frontend" / "data" / "query_grids" / f"{layer_id}_{year}.json",
        project_root / "frontend" / "data" / "query_grids" / "four_dim" / f"{layer_id}_{year}.json",
        project_root / "frontend" / "data" / "overlays" / f"{layer_id}_{year}.png",
        project_root / "frontend" / "data" / "overlays" / "four_dim" / f"{layer_id}_{year}.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.relative_to(project_root))
    return str(stat.get("source") or stat.get("overlay") or "项目本地统计配置")


def build_data_answer(user_text: str, year: int | None = None, layer_id: str | None = None) -> str | None:
    """对明确的数据统计问题直接基于项目 JSON 返回确定答案。"""
    if is_method_question(user_text) or is_regional_extreme_question(user_text):
        return None
    years = detect_years(user_text) or ([year] if year else [])
    layers = detect_layers(user_text, layer_id)
    metrics = detect_metrics(user_text)
    if not years or not layers:
        return None
    if not metrics:
        metrics = ["median", "mean", "min", "max", "p90", "validRatio"]

    lines: list[str] = ["我已从项目本地数据统计中读取到以下结果："]
    found = False
    for target_year in years:
        for target_layer in layers:
            stat = timeline_stat(target_year, target_layer)
            if not stat or stat.get("available") is False:
                lines.append(f"- {target_year} 年 {layer_label(target_layer)}（{target_layer}）：暂无可用统计。")
                continue
            found = True
            parts = []
            for metric in metrics:
                raw = stat.get(metric)
                if raw is None and metric == "validRatio":
                    raw = stat.get("valid_ratio")
                parts.append(f"{metric}={_format_value(metric, raw)}")
            lines.append(f"- {target_year} 年 {layer_label(target_layer)}（{target_layer}）：" + "，".join(parts) + "。")
    if not found:
        return "我在项目数据统计中没有找到你问题对应的可用图层/年份，请确认年份和图层名称。"
    lines.append("\n说明：这些数值来自项目内统计配置和本地数据文件，不是模型凭空生成。")
    return "\n".join(lines)


def build_question_context(user_text: str, year: int | None = None, layer_id: str | None = None) -> str:
    """根据用户问题挑选相关年份和图层统计，作为大模型上下文。"""
    summary = load_summary()
    years = detect_analysis_years(user_text, year)
    layers = detect_layers(user_text, layer_id)
    if not layers:
        layers = [layer.get("id") for layer in summary.get("layers", []) if layer.get("id")]
    metrics = ["median", "mean", "min", "max", "p90", "validRatio", "valid_ratio"]

    lines = ["\n与用户问题直接相关的项目本地数据统计："]
    for target_year in years:
        lines.append(f"{target_year} 年：")
        for target_layer in layers:
            stat = timeline_stat(target_year, target_layer)
            if not isinstance(stat, dict) or stat.get("available") is False:
                continue
            values = []
            for metric in metrics:
                if metric in stat:
                    values.append(f"{metric}={stat.get(metric)}")
            lines.append(f"- {target_layer}（{layer_label(target_layer)}）：" + ", ".join(values))
    return "\n".join(lines)


def _available_years() -> list[int]:
    years = {int(y) for y in load_summary().get("years", [])}
    years.update(int(y) for y in load_supplemental_stats().keys() if str(y).isdigit())
    return sorted(years)


def _is_trend_question(text: str) -> bool:
    lowered = text.lower()
    keywords = ["变化", "趋势", "演变", "多年", "对比", "比较", "关系", "相关", "2000到", "2000-", "trend", "compare", "relationship"]
    return any(keyword in lowered for keyword in keywords)


def _metric_number(stat: dict[str, Any], metric: str) -> float | None:
    raw = stat.get(metric)
    if raw is None and metric == "validRatio":
        raw = stat.get("valid_ratio")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _trend_sentence(layer_id: str, series: list[tuple[int, float]], metric: str) -> str:
    if not series:
        return f"{layer_label(layer_id)}（{layer_id}）暂无可用序列。"
    start_year, start_value = series[0]
    end_year, end_value = series[-1]
    delta = end_value - start_value
    rate = (delta / abs(start_value) * 100) if start_value else None
    direction = "上升" if delta > 0 else "下降" if delta < 0 else "基本持平"
    values = "；".join(f"{year}:{value:.4f}" for year, value in series)
    rate_text = f"，相对变化 {rate:.2f}%" if rate is not None else ""
    return (
        f"{layer_label(layer_id)}（{layer_id}）{metric} 序列为 {values}。"
        f"从 {start_year} 年到 {end_year} 年{direction}，变化量 {delta:.4f}{rate_text}。"
    )


def build_trend_answer(user_text: str, year: int | None = None, layer_id: str | None = None) -> str | None:
    """对多年变化、对比和关系类问题给出本地统计摘要，供前端直接展示或交给大模型延展。"""
    if is_method_question(user_text):
        return None
    if not _is_trend_question(user_text):
        return None
    layers = detect_layers(user_text, layer_id)
    if not layers:
        return None
    years = detect_analysis_years(user_text, year)
    metrics = detect_metrics(user_text) or ["median"]
    metric = metrics[0]

    lines = ["我先基于项目本地统计整理出多年序列："]
    found_any = False
    for target_layer in layers:
        series: list[tuple[int, float]] = []
        for target_year in years:
            stat = timeline_stat(target_year, target_layer)
            if not isinstance(stat, dict) or stat.get("available") is False:
                continue
            value = _metric_number(stat, metric)
            if value is not None:
                series.append((target_year, value))
        if series:
            found_any = True
            lines.append(f"- {_trend_sentence(target_layer, series, metric)}")
    if not found_any:
        return None

    if len(layers) >= 2:
        lines.append("\n对比解读：以上序列可用于判断不同指标是否同向变化；若一个指标上升、另一个下降，通常提示生态过程与人类活动或风险因子之间存在差异化响应。")
    lines.append("\n说明：以上序列来自项目内统计配置和本地数据文件；如果需要空间分布细节，可继续指定年份、图层或经纬度点位。")
    return "\n".join(lines)


def sample_query_grid(layer_id: str, year: int, lon: float, lat: float) -> float | None:
    """在服务端按经纬度采样查询网格，与前端逻辑保持一致。"""
    data_dir = get_settings().data_path
    candidates = [
        data_dir / "query_grids" / f"{layer_id}_{year}.json",
        data_dir / "query_grids" / "four_dim" / f"{layer_id}_{year}.json",
    ]
    grid_path = next((p for p in candidates if p.exists()), None)
    if grid_path is None:
        return None

    grid = json.loads(grid_path.read_text(encoding="utf-8"))
    bounds = grid["bounds"]
    west, south, east, north = bounds["west"], bounds["south"], bounds["east"], bounds["north"]
    if lon < west or lon > east or lat < south or lat > north:
        return None

    width, height = grid["width"], grid["height"]
    x = round((lon - west) / (east - west) * (width - 1))
    y = round((north - lat) / (north - south) * (height - 1))
    try:
        return grid["values"][y][x]
    except (IndexError, TypeError):
        return None


def build_llm_context(year: int | None = None, layer_id: str | None = None, user_text: str = "") -> str:
    """把当前研究区与图层统计整理成给大模型的中文背景。"""
    summary = load_summary()
    bounds = summary.get("bounds", {})
    years = summary.get("years", [])
    layers = summary.get("layers", [])

    lines: list[str] = []
    lines.append("你是『黄河滩区生态韧性数智平台』的分析助手，研究区为黄河中下游（河南段）滩区。")
    lines.append(
        f"研究区范围：经度 {bounds.get('west')}~{bounds.get('east')}，纬度 {bounds.get('south')}~{bounds.get('north')}。"
    )
    lines.append(f"可用年份：{years}。")
    lines.append("图层清单：")
    for layer in layers:
        lines.append(f"- {layer.get('id')}（{layer.get('label')}）：{layer.get('description', '')}")

    target_year = year or (years[-1] if years else None)
    if target_year is not None:
        lines.append(f"\n{target_year} 年各图层统计（中位数/最小/最大/有效像元比例）：")
        layer_ids = list({
            *summary.get("timeline", {}).get(str(target_year), {}).keys(),
            *load_supplemental_stats().get(str(target_year), {}).keys(),
        })
        for lid in layer_ids:
            stat = timeline_stat(target_year, lid)
            if not isinstance(stat, dict):
                continue
            lines.append(
                f"- {lid}：median={stat.get('median')}, min={stat.get('min')}, "
                f"max={stat.get('max')}, validRatio={stat.get('validRatio') or stat.get('valid_ratio')}"
            )

    if layer_id:
        lines.append(f"\n用户当前关注图层：{layer_id}（{layer_label(layer_id)}）。")

    if user_text and not is_method_question(user_text):
        lines.append(build_question_context(user_text, year, layer_id))

    lines.append(
        "\n请基于上述真实统计作答，使用简洁中文，必要时给出生态治理或风险预警建议；"
        "如果问题询问中位数、均值、最大值、最小值、有效像元比例等统计量，必须直接引用上下文中的数值；"
        "不要说无法访问项目数据，因为后端已经把项目本地统计结果提供给你；"
        "不要在最终回答中输出本地文件路径；"
        "如果用户询问县域或区域最高最低，而上下文没有县级分区统计，不要用全区像元最大值冒充县域平均值；"
        "不要编造研究区不存在的数据。"
    )
    return "\n".join(lines)
