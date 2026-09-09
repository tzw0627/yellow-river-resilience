from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from .config import get_settings
from .context import load_summary, sample_query_grid, timeline_stat

AgentIntent = Literal[
    "concept_explain",
    "stats_query",
    "spatial_analysis",
    "governance_advice",
    "teaching_guidance",
    "report_generation",
    "general_chat",
]

LAYER_LABELS: dict[str, str] = {
    "ndvi": "NDVI 植被覆盖",
    "evi": "EVI 植被活力",
    "clcd": "CLCD 土地利用",
    "water": "水体频率",
    "ntl": "夜间灯光",
    "gdp": "GDP 空间强度",
    "ri": "生态韧性指数 RI",
    "four_dim_er": "综合生态韧性 ER",
    "four_dim_ers": "规模韧性 ERS",
    "four_dim_erd": "密度韧性 ERD",
    "four_dim_erm": "形态韧性 ERM",
    "four_dim_erf": "洪水韧性 ERF",
    "four_dim_fri": "洪水风险 FRI",
}

LAYER_ALIASES: dict[str, tuple[str, ...]] = {
    "ndvi": ("ndvi", "植被指数", "植被覆盖", "归一化植被"),
    "evi": ("evi", "增强型植被", "植被活力"),
    "clcd": ("clcd", "土地利用", "土地覆盖", "建设用地", "耕地"),
    "water": ("water", "水体", "水域", "水体频率"),
    "ntl": ("ntl", "夜间灯光", "灯光", "人类活动"),
    "gdp": ("gdp", "经济", "生产总值"),
    "ri": ("ri", "生态韧性指数", "韧性指数"),
    "four_dim_er": ("four_dim_er", "综合韧性", "综合生态韧性", "er"),
    "four_dim_ers": ("four_dim_ers", "规模韧性", "ers"),
    "four_dim_erd": ("four_dim_erd", "密度韧性", "erd"),
    "four_dim_erm": ("four_dim_erm", "形态韧性", "erm"),
    "four_dim_erf": ("four_dim_erf", "洪水韧性", "erf"),
    "four_dim_fri": ("four_dim_fri", "洪水风险", "fri", "风险"),
}

METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "median": ("中位数", "中值", "median"),
    "mean": ("平均值", "均值", "mean", "average"),
    "min": ("最小值", "最低值", "min"),
    "max": ("最大值", "最高值", "max"),
    "p90": ("p90", "90分位", "90 分位", "第90百分位", "百分之90", "90%"),
    "validRatio": ("有效像元比例", "有效比例", "validratio", "valid ratio"),
}

METRIC_LABELS: dict[str, str] = {
    "median": "中位数",
    "mean": "平均值",
    "min": "最小值",
    "max": "最大值",
    "p90": "P90",
    "validRatio": "有效像元比例",
}


def _contains_any(text: str, keywords: tuple[str, ...] | list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def classifyIntent(question: str) -> AgentIntent:
    text = question.strip().lower()
    if not text:
        return "general_chat"

    if _contains_any(text, ("生成报告", "导出报告", "报告怎么写", "报告生成", "下载报告")):
        return "report_generation"
    if _contains_any(text, ("学生", "课堂", "教学", "课程", "这节课", "学习", "作业", "如何分析这张图", "怎么讲")):
        return "teaching_guidance"
    if _contains_any(text, ("治理", "修复", "管控", "建议", "措施", "怎么治", "怎么办", "防洪", "风险高的地方")):
        return "governance_advice"
    if _contains_any(text, ("中位数", "平均值", "均值", "最大值", "最小值", "最高值", "最低值", "p90", "90分位", "有效像元", "是多少")):
        return "stats_query"
    if _contains_any(text, ("哪里", "哪些地方", "空间", "分布", "这里", "这个地方", "为什么", "原因", "韧性低", "风险高")):
        return "spatial_analysis"
    if _contains_any(text, ("什么是", "是什么意思", "代表什么", "含义", "概念", "定义", "解释一下")):
        return "concept_explain"
    return "general_chat"


def _detect_years(question: str, fallback_year: int | None) -> list[int]:
    years = [int(item) for item in re.findall(r"(?:19|20)\d{2}", question)]
    if years:
        return list(dict.fromkeys(years))
    if fallback_year:
        return [fallback_year]
    summary_years = [int(year) for year in load_summary().get("years", []) if str(year).isdigit()]
    return [summary_years[-1]] if summary_years else []


def _detect_layers(question: str, fallback_layer: str | None) -> list[str]:
    lowered = question.lower()
    layers: list[str] = []
    for layer_id, aliases in LAYER_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            layers.append(layer_id)
    if not layers and fallback_layer:
        layers.append(fallback_layer)
    return list(dict.fromkeys(layers))


def _detect_metrics(question: str) -> list[str]:
    lowered = question.lower()
    metrics: list[str] = []
    for metric, aliases in METRIC_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            metrics.append(metric)
    return list(dict.fromkeys(metrics))


def _clean_layer_label(layer_id: str) -> str:
    return LAYER_LABELS.get(layer_id, layer_id)


def _metric_value(stat: dict[str, Any], metric: str) -> Any:
    if metric == "validRatio":
        return stat.get("validRatio", stat.get("valid_ratio"))
    return stat.get(metric)


def _format_metric(metric: str, value: Any) -> str:
    if value is None:
        return "暂无数据"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if metric == "validRatio":
        return f"{number * 100:.1f}%"
    return f"{number:.4f}"


def _layer_meaning(layer_id: str) -> str:
    if layer_id == "ndvi":
        return "NDVI 越高通常表示植被覆盖和生长状况越好；过低可能提示裸地、建设用地、水体或植被退化。"
    if layer_id == "evi":
        return "EVI 更强调植被活力，对高覆盖植被区比 NDVI 更不容易饱和。"
    if layer_id == "four_dim_fri":
        return "FRI 越高表示洪水风险越高，需要结合地形、水体频率和土地利用风险共同判断。"
    if layer_id in {"ri", "four_dim_er", "four_dim_erd", "four_dim_ers", "four_dim_erm", "four_dim_erf"}:
        return "韧性类指标通常越高表示生态系统承受扰动、恢复和维持功能的能力越强；低值区更值得核查。"
    if layer_id == "clcd":
        return "土地利用图层用于识别建设用地、耕地、水体和生态用地格局，是解释风险来源的重要证据。"
    if layer_id == "ntl":
        return "夜间灯光可作为人类活动强度的代理变量，灯光增强常提示建设和活动压力上升。"
    if layer_id == "gdp":
        return "GDP 空间强度反映经济活动暴露度，常用于辅助判断风险承载对象。"
    return "该指标需要结合图层说明、空间位置和其他因子共同解释。"


def getLocalStats(question: str, year: int | None = None, layer: str | None = None) -> list[dict[str, Any]]:
    years = _detect_years(question, year)
    layers = _detect_layers(question, layer)
    metrics = _detect_metrics(question) or ["median", "mean", "min", "max", "p90", "validRatio"]
    rows: list[dict[str, Any]] = []
    for target_year in years:
        for target_layer in layers:
            stat = timeline_stat(target_year, target_layer)
            if not isinstance(stat, dict) or stat.get("available") is False:
                rows.append({
                    "year": target_year,
                    "layer": target_layer,
                    "label": _clean_layer_label(target_layer),
                    "available": False,
                    "metrics": {},
                })
                continue
            values = {metric: _metric_value(stat, metric) for metric in metrics}
            rows.append({
                "year": target_year,
                "layer": target_layer,
                "label": _clean_layer_label(target_layer),
                "available": True,
                "metrics": values,
                "raw": stat,
            })
    return rows


@lru_cache
def _load_region_analysis() -> dict[str, Any]:
    path = get_settings().data_path / "region_analysis.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _region_context(region_id: str | None) -> dict[str, Any] | None:
    if not region_id:
        return None
    payload = _load_region_analysis()
    regions = payload.get("regions", {})
    region = regions.get(region_id)
    if isinstance(region, dict):
        return region
    return None


def _sample_current_grid(year: int | None, layer: str | None, query: dict[str, Any] | None) -> float | None:
    if not year or not layer or not query:
        return None
    lon = query.get("lon")
    lat = query.get("lat")
    if lon is None or lat is None:
        return None
    try:
        return sample_query_grid(layer, int(year), float(lon), float(lat))
    except Exception:  # noqa: BLE001
        return None


def buildAgentContext(
    intent: AgentIntent,
    question: str,
    year: int | None,
    layer: str | None,
    region_id: str | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stats = getLocalStats(question, year, layer) if intent in {
        "stats_query",
        "spatial_analysis",
        "governance_advice",
        "teaching_guidance",
        "report_generation",
    } else []
    return {
        "intent": intent,
        "question": question,
        "year": year,
        "layer": layer,
        "layerLabel": _clean_layer_label(layer) if layer else None,
        "stats": stats,
        "regionId": region_id,
        "regionAnalysis": _region_context(region_id),
        "query": query,
        "sampledValue": _sample_current_grid(year, layer, query),
    }


def _concept_answer(question: str, context: dict[str, Any]) -> str:
    lowered = question.lower()
    if "fri" in lowered or "洪水风险" in question:
        return (
            "FRI 是洪水风险指数，用来表达某个位置或像元受到洪水扰动的相对风险。"
            "在本平台中，FRI 综合了低高程风险、低坡度风险、水体相关风险和土地利用风险；数值越高，通常表示洪水风险越高。"
            "它不是生态韧性本身，而是解释韧性压力来源的重要证据。"
        )
    if "erd" in lowered or "密度韧性" in question:
        return (
            "ERD 表示密度韧性，关注生态承载能力与人类活动压力之间的关系。"
            "在平台语境下，可以把它理解为：生态用地、植被等支撑越强，人类活动压力越低，ERD 越有利；反之则提示密度格局可能削弱生态韧性。"
        )
    if re.search(r"\ber\b", lowered) or "综合韧性" in question:
        return (
            "ER 是综合生态韧性指标，整合规模韧性、密度韧性、形态韧性和洪水韧性等维度。"
            "它用于概括滩区生态系统面对扰动时的承受、恢复和维持功能的能力；通常数值越高，韧性越强。"
        )
    if "p90" in lowered or "90" in question:
        return _stats_answer(question, context)
    return (
        "生态韧性指生态系统在受到洪水、土地利用变化、人类活动压力等扰动时，仍能维持关键结构与功能，并在扰动后恢复的能力。"
        "在这个平台里，它不是单一数值，而是通过植被状态、土地利用、水体、夜间灯光、GDP、人类活动压力以及 ER/ERD/FRI 等指标共同分析。"
        "因此，解释韧性时应同时看数值大小、空间位置、风险来源和治理场景。"
    )


def _stats_answer(question: str, context: dict[str, Any]) -> str:
    stats = context.get("stats") or getLocalStats(question, context.get("year"), context.get("layer"))
    if not stats:
        return "我没有在当前问题中识别到明确的年份或图层。请补充例如“2024年 NDVI 中位数”这样的年份、图层和统计量。"

    lines: list[str] = []
    for row in stats:
        label = row["label"]
        year = row["year"]
        layer = row["layer"]
        if not row.get("available"):
            lines.append(f"{year} 年 {label}（{layer}）当前没有可用统计结果。")
            continue
        metrics = row.get("metrics", {})
        metric_parts = [f"{METRIC_LABELS.get(metric, metric)}为 {_format_metric(metric, value)}" for metric, value in metrics.items()]
        lines.append(f"根据当前系统加载的 {year} 年 {label} 统计结果，" + "，".join(metric_parts) + "。")
        if "p90" in metrics:
            lines.append("P90 表示第 90 百分位数：约有 90% 的有效像元不高于这个值，剩余约 10% 的像元处在更高水平，可用于识别高值尾部区域。")
        if "median" in metrics:
            lines.append("中位数比平均值更不容易被极端像元影响，适合描述研究区内该指标的典型水平。")
        if "validRatio" in metrics:
            lines.append("有效像元比例反映参与统计的像元占比；比例较低时，解读结果要注意数据覆盖范围。")
        lines.append(_layer_meaning(layer))
    return "\n".join(lines)


def _spatial_answer(question: str, context: dict[str, Any]) -> str:
    layer = context.get("layer") or "ndvi"
    label = context.get("layerLabel") or _clean_layer_label(layer)
    query = context.get("query") or {}
    sampled = context.get("sampledValue")
    stats = context.get("stats") or []
    stat = next((row for row in stats if row.get("available")), None)
    lines = [f"空间分析要先把当前图层“{label}”当作证据，而不是只看一个汇总数。"]
    if query:
        value = sampled if sampled is not None else query.get("value")
        place = query.get("place") or "当前点击位置"
        if value is not None:
            lines.append(f"你当前关注的 {place} 附近，{label} 的采样值约为 {float(value):.4f}。这可以作为点位证据，但不能直接代表整个区县。")
    if stat:
        median = _format_metric("median", stat.get("metrics", {}).get("median", stat.get("raw", {}).get("median")))
        p90 = _format_metric("p90", stat.get("metrics", {}).get("p90", stat.get("raw", {}).get("p90")))
        lines.append(f"全区统计可作为背景参照：{stat['year']} 年 {stat['label']} 的中位数约为 {median}，P90 约为 {p90}。")
    lines.append(
        "判断“哪些地方韧性低/风险高”时，建议叠加核查：低 ER 或 ERD、较高 FRI、建设用地扩张、夜间灯光增强、GDP 或人口暴露较高、植被指数偏低等信号。"
    )
    lines.append("如果需要指出具体区县，需要使用区县边界做分区统计；仅凭全区像元最大/最小值，不能冒充区县平均最高或最低。")
    return "\n".join(lines)


def _governance_answer(question: str, context: dict[str, Any]) -> str:
    return (
        "洪水风险高的地方应按“风险识别-暴露控制-生态缓冲-应急管理”来治理：\n"
        "1. 先用 FRI 定位高洪水风险斑块，再与 ER、ERD 对照，优先处理“高 FRI + 低韧性”的重叠区域。\n"
        "2. 结合 CLCD 土地利用核查建设用地、耕地和水体边界，限制高风险带新增建设，保留行洪通道和滞蓄空间。\n"
        "3. 对植被支撑弱的区域，用 NDVI/EVI 核验生态质量，优先恢复滩地植被、湿地缓冲带和岸线生态廊道。\n"
        "4. 对夜间灯光、GDP 或人口暴露较高的区域，强化预警、避险路线、关键设施防护和分区管控。\n"
        "5. 注意限制条件：当前平台统计主要来自栅格和已有分区结果，具体工程措施还需要结合实测水文、地形高程、堤防条件和现场调查。"
    )


def _teaching_answer(question: str, context: dict[str, Any]) -> str:
    return (
        "可以把这张图设计成一节“证据链式”分析课：\n"
        "1. 先让学生说明 ER、ERD 和 FRI 的含义：ER/ERD关注生态韧性，FRI关注洪水风险，二者方向不同。\n"
        "2. 选择同一年份，例如 2024 年，先读图层中位数、P90 和有效像元比例，判断全区背景水平。\n"
        "3. 切换 ER 与 FRI，寻找“低 ER/ERD + 高 FRI”的空间重叠区，并要求学生截图或记录证据。\n"
        "4. 再叠加 NDVI/EVI、CLCD、夜间灯光和 GDP，解释低韧性或高风险可能来自植被不足、建设压力、水体邻近或人类活动增强。\n"
        "5. 最后形成学习报告：写清问题、使用的图层、关键数值、空间证据、治理建议和不确定性，避免只凭单一颜色下结论。"
    )


def _report_answer(question: str, context: dict[str, Any]) -> str:
    return (
        "报告生成可以按右侧“报告”面板完成：选择年份、勾选需要纳入的图层，再导出 Word 或 PDF。"
        "内容上建议包含：研究区与数据来源、核心图层统计、空间发现、风险解释、治理建议和不确定性说明。"
        "如果是课程作业，还应附上图层切换和点位核验过程。"
    )


def _general_answer(question: str, context: dict[str, Any]) -> str:
    return (
        "我可以围绕这个黄河滩区平台回答概念解释、图层统计、空间分析、治理建议、教学设计和报告写作。"
        "你可以直接问“2024年NDVI中位数是多少”“FRI是什么意思”“洪水风险高的地方怎么治理”或“学生如何分析ER和FRI”。"
    )


def buildAgentAnswer(
    intent: AgentIntent,
    question: str,
    context: dict[str, Any],
    stats: list[dict[str, Any]] | None = None,
    model_reply: str | None = None,
) -> str:
    if stats is not None:
        context = {**context, "stats": stats}

    if model_reply and intent not in {"stats_query"}:
        return model_reply.strip()

    if intent == "concept_explain":
        return _concept_answer(question, context)
    if intent == "stats_query":
        return _stats_answer(question, context)
    if intent == "spatial_analysis":
        return _spatial_answer(question, context)
    if intent == "governance_advice":
        return _governance_answer(question, context)
    if intent == "teaching_guidance":
        return _teaching_answer(question, context)
    if intent == "report_generation":
        return _report_answer(question, context)
    return _general_answer(question, context)


def buildAgentMessages(question: str, context: dict[str, Any], history: list[dict[str, str]]) -> list[dict[str, str]]:
    stats_lines: list[str] = []
    for row in context.get("stats") or []:
        if not row.get("available"):
            continue
        values = ", ".join(
            f"{METRIC_LABELS.get(metric, metric)}={_format_metric(metric, value)}"
            for metric, value in row.get("metrics", {}).items()
        )
        stats_lines.append(f"- {row['year']}年 {row['label']}：{values}")

    system = (
        "你是黄河滩区生态韧性平台的问答助手。必须先理解用户原问题，再判断是否需要本地数据。"
        "本地统计只能作为证据融入回答，不能把固定统计模板当作所有问题的答案。"
        f"\n当前意图：{context.get('intent')}"
        f"\n当前年份：{context.get('year')}；当前图层：{context.get('layerLabel') or context.get('layer')}"
        f"\n当前点击点：{context.get('query') or '无'}"
        "\n本地统计证据：\n" + ("\n".join(stats_lines) if stats_lines else "本问题未要求直接引用统计值。") +
        "\n回答要求：概念类回答概念；统计类引用数值并解释含义；空间类说明证据链和限制；治理类给出分区治理建议；教学类给出步骤。不要输出本地文件路径。"
    )
    return [{"role": "system", "content": system}, *history, {"role": "user", "content": question}]
