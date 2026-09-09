from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .active_analysis import build_active_analysis_context
from .config import get_settings
from .context import (
    LAYER_ALIASES,
    METRIC_ALIASES,
    build_data_answer,
    build_question_context,
    build_trend_answer,
    detect_analysis_years,
    detect_layers,
    detect_metrics,
    is_method_question,
    is_regional_extreme_question,
    layer_label,
    load_supplemental_stats,
    load_summary,
    timeline_stat,
)


@dataclass(frozen=True)
class RagDocument:
    id: str
    title: str
    text: str
    layer: str | None = None
    year: int | None = None
    source: str | None = None


def _project_root() -> Path:
    return get_settings().data_path.parent.parent


def _tokenize(text: str) -> set[str]:
    lowered = text.lower()
    tokens = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*|(?:19|20)\d{2}|[\u4e00-\u9fff]{2,}", lowered))
    for layer_id, aliases in LAYER_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            tokens.add(layer_id)
    for metric, aliases in METRIC_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            tokens.add(metric.lower())
    return tokens


def _source_candidates(layer_id: str, year: int | str) -> list[Path]:
    root = _project_root()
    return [
        root / "data" / "processed" / "aligned" / f"{layer_id}_{year}_epsg4326_250m.tif",
        root / "data" / "processed" / "four_dim_aligned" / str(year) / f"{layer_id.replace('four_dim_', '')}_{year}.tif",
        root / "frontend" / "data" / "query_grids" / f"{layer_id}_{year}.json",
        root / "frontend" / "data" / "query_grids" / "four_dim" / f"{layer_id}_{year}.json",
        root / "frontend" / "data" / "overlays" / f"{layer_id}_{year}.png",
        root / "frontend" / "data" / "overlays" / "four_dim" / f"{layer_id}_{year}.png",
    ]


def _existing_sources(layer_id: str, year: int | str) -> list[str]:
    root = _project_root()
    sources: list[str] = []
    for path in _source_candidates(layer_id, year):
        if path.exists():
            sources.append(str(path.relative_to(root)))
    return sources


def _all_year_keys() -> list[str]:
    years = {str(year) for year in load_summary().get("years", [])}
    years.update(load_summary().get("timeline", {}).keys())
    years.update(load_supplemental_stats().keys())
    return sorted(years, key=lambda item: int(item) if item.isdigit() else 9999)


@lru_cache
def build_rag_index() -> tuple[RagDocument, ...]:
    docs: list[RagDocument] = []
    summary = load_summary()

    bounds = summary.get("bounds", {})
    docs.append(
        RagDocument(
            id="study-area",
            title="研究区与可用数据总览",
            text=(
                "研究区为黄河中下游河南段滩区。"
                f"空间范围：west={bounds.get('west')}, south={bounds.get('south')}, "
                f"east={bounds.get('east')}, north={bounds.get('north')}。"
                f"可用年份：{_all_year_keys()}。"
                "项目包含 NDVI、EVI、CLCD土地利用、夜间灯光NTL、GDP、水体、人口、TerraClimate、"
                "四维综合生态韧性、规模韧性、密度韧性、形态韧性、洪水韧性、洪水风险等图层。"
            ),
            source="frontend/data/layer_summary.json; web/src/config/generated/layerStatsAligned.ts",
        )
    )

    docs.append(
        RagDocument(
            id="method:resilience-calculation",
            title="生态韧性计算方法与指标体系",
            text=(
                "项目包含两套生态韧性计算方法。"
                "第一套是 MVP 生态韧性指数：先把 NDVI、EVI、水体频率、CLCD生态赋分组成 resistance 抵抗力；"
                "用 NDVI/EVI 当前年相对 2000 年的变化组成 recovery 恢复力；"
                "用 log1p(GDP)、log1p(人口) 和反向归一化 log1p(夜间灯光) 组成 adaptation 适应力；"
                "最后 resilience_index = resistance、recovery、adaptation 的像元均值。"
                "归一化使用 2% 和 98% 分位数截尾的 robust normalization，nodata 不参与计算。"
                "第二套是四维生态韧性：ER 由 ERS、ERD、ERM、ERF 四个维度等权综合，"
                "即 ER_raw = 0.25*ERS + 0.25*ERD + 0.25*ERM + 0.25*ERF，并结合植被因子后再归一化到 0-1。"
                "ERS 表示规模韧性，由生态用地/高植被像元邻域比例与建设用地邻域比例计算；"
                "ERD 表示密度韧性，由 CLCD生态承载赋分 ECC 与人类活动压力 HAP 计算，ERD = ECC / (ECC + HAP + EPS)；"
                "ERM 表示形态韧性，利用到生态源/汇像元的距离衰减 exp(-distance/1000) 表示空间形态连通性；"
                "FRI 表示洪水风险，FRI = 0.30*低高程风险 + 0.20*低坡度风险 + 0.30*水体风险 + 0.20*土地利用风险；"
                "ERF 表示洪水韧性，ERF = 1 - FRI。"
            ),
            source="backend/scripts/compute_resilience_index.py; backend/scripts/calc_four_dim_from_local_dataset.py",
        )
    )

    layer_ids: set[str] = set()
    for year_key in _all_year_keys():
        layer_ids.update(load_summary().get("timeline", {}).get(year_key, {}).keys())
        layer_ids.update(load_supplemental_stats().get(year_key, {}).keys())

    for year_key in _all_year_keys():
        for layer_id in sorted(layer_ids):
            stat = timeline_stat(year_key, layer_id)
            if not isinstance(stat, dict) or stat.get("available") is False:
                continue
            sources = _existing_sources(layer_id, year_key)
            label = layer_label(layer_id)
            stat_text = (
                f"年份：{year_key}。图层：{layer_id}（{label}）。"
                f"available={stat.get('available')}; "
                f"median={stat.get('median')}; mean={stat.get('mean')}; "
                f"min={stat.get('min')}; max={stat.get('max')}; p90={stat.get('p90')}; "
                f"validRatio={stat.get('validRatio') or stat.get('valid_ratio')}; "
                f"sourceYear={stat.get('sourceYear') or stat.get('source_year')}。"
                "这些统计用于模型分析，回答时不需要暴露本地文件路径。"
            )
            docs.append(
                RagDocument(
                    id=f"stat:{year_key}:{layer_id}",
                    title=f"{year_key} 年 {label} 统计",
                    text=stat_text,
                    layer=layer_id,
                    year=int(year_key) if year_key.isdigit() else None,
                    source="; ".join(sources) if sources else "项目统计配置",
                )
            )

    for rel in [
        "docs/data_inventory.csv",
        "docs/processed_inventory.csv",
        "docs/processed_quality_report.md",
        "docs/processing_standard.md",
        "docs/four_dim_2020_cesium_integration_report.md",
        "backend/scripts/compute_resilience_index.py",
        "backend/scripts/calc_four_dim_from_local_dataset.py",
    ]:
        path = _project_root() / rel
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")[:6000]
            docs.append(RagDocument(id=f"doc:{rel}", title=rel, text=text, source=rel))

    return tuple(docs)


def retrieve_rag_documents(query: str, year: int | None = None, layer: str | None = None, top_k: int = 10) -> list[RagDocument]:
    docs = build_rag_index()
    query_tokens = _tokenize(query)
    method_query = is_method_question(query)
    query_years = set(detect_analysis_years(query, year))
    query_layers = set(detect_layers(query, None if method_query else layer))
    query_metrics = {metric.lower() for metric in detect_metrics(query)}

    scored: list[tuple[float, RagDocument]] = []
    for doc in docs:
        doc_tokens = _tokenize(doc.title + "\n" + doc.text)
        score = float(len(query_tokens & doc_tokens))
        if doc.year is not None and doc.year in query_years:
            score += 4.0
        if doc.layer and doc.layer in query_layers:
            score += 5.0
        if query_metrics and any(metric in doc.text.lower() for metric in query_metrics):
            score += 2.0
        if doc.id == "study-area":
            score += 0.5
        if method_query and (doc.id.startswith("method:") or "compute_resilience" in doc.id or "calc_four_dim" in doc.id or "processing_standard" in doc.id):
            score += 12.0
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def build_rag_context(query: str, year: int | None = None, layer: str | None = None) -> str:
    docs = retrieve_rag_documents(query, year, layer)
    trend = build_trend_answer(query, year, layer)
    exact = build_data_answer(query, year, layer)
    question_stats = "" if is_method_question(query) else build_question_context(query, year, layer)
    active_analysis = build_active_analysis_context(query, year, layer)

    lines = ["以下是本地 RAG 检索到的项目数据上下文，必须优先依据这些内容回答："]
    if active_analysis:
        lines.append(active_analysis)
    if is_regional_extreme_question(query):
        lines.append(
            "\n[区域/县域问题约束]\n"
            "当前项目 RAG 未检索到县域行政边界或县级 zonal statistics 分区统计结果。"
            "如果用户询问‘哪个县平均最高/最低’，不能把全区像元 max/min 当作县域平均值回答，"
            "应说明当前只能提供研究区整体统计和空间图层依据；若要得到县名，需要先用县域边界对栅格做分区统计。"
            "回答时不要输出本地文件路径。"
        )
    if exact:
        lines.append("\n[确定性统计结果]\n" + exact)
    if trend:
        lines.append("\n[多年序列/趋势检索结果]\n" + trend)
    if question_stats:
        lines.append("\n[相关图层统计上下文]\n" + question_stats)
    if active_analysis:
        lines.append(active_analysis)
    lines.append("\n[召回文档]")
    for idx, doc in enumerate(docs, 1):
        lines.append(f"{idx}. {doc.title}\n内容：{doc.text}")

    lines.append(
        "\n回答要求："
        "1. 先说明已基于项目本地 RAG 检索到的数据进行分析，但不要输出本地文件路径；"
        "2. 涉及数值时引用检索上下文中的年份、图层和统计值；"
        "3. 不要只复述检索结果，要根据用户问题主动分析生态含义、风险含义或治理意义；"
        "4. 如果主动计算分析结果可用，必须按‘RAG检索—可计算性判断—主动计算—结论/建议’组织答案；"
        "5. 若用户问县域/区域最高最低，而上下文没有县级分区统计，必须说明目前缺少县域 zonal statistics，不能用全区像元最大值冒充县平均最高；"
        "6. 不要声称无法访问项目数据；若上下文没有某项数据，要说明缺少哪一年/哪一图层/哪类分区统计。"
    )
    return "\n".join(lines)


def rag_status() -> dict[str, Any]:
    docs = build_rag_index()
    layers = sorted({doc.layer for doc in docs if doc.layer})
    years = sorted({doc.year for doc in docs if doc.year})
    return {"documents": len(docs), "layers": layers, "years": years}
