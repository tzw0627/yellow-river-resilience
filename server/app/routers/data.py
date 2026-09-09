from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..context import (
    layer_label,
    load_summary,
    load_twin,
    sample_query_grid,
    timeline_stat,
)

router = APIRouter(prefix="/api", tags=["data"])


class QueryRequest(BaseModel):
    layer: str
    year: int
    lon: float
    lat: float


class QueryResponse(BaseModel):
    layer: str
    label: str
    year: int
    lon: float
    lat: float
    value: float | None
    explanation: str


def _explain(layer: str, value: float | None) -> str:
    if value is None:
        return "该位置暂无有效数据。"
    if layer == "four_dim_fri":
        if value >= 0.7:
            return f"FRI 为 {value:.3f}，洪水风险较高。"
        if value >= 0.4:
            return f"FRI 为 {value:.3f}，洪水风险中等。"
        return f"FRI 为 {value:.3f}，洪水风险较低。"
    if layer.startswith("four_dim_") or layer == "ri":
        if value >= 0.7:
            return f"指数 {value:.3f}，该位置生态韧性较强。"
        if value >= 0.4:
            return f"指数 {value:.3f}，该位置生态韧性中等。"
        return f"指数 {value:.3f}，该位置生态韧性较弱。"
    if layer in {"ndvi", "evi"}:
        if value >= 0.55:
            return f"植被指数 {value:.3f}，植被状态较好。"
        if value >= 0.3:
            return f"植被指数 {value:.3f}，植被状态中等。"
        return f"植被指数 {value:.3f}，植被偏弱。"
    return f"该位置当前图层值为 {value:.3f}。"


@router.get("/summary")
def get_summary() -> dict:
    summary = load_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="layer_summary.json 未找到")
    return summary


@router.get("/twin")
def get_twin() -> dict:
    twin = load_twin()
    if not twin:
        raise HTTPException(status_code=404, detail="twin_model.json 未找到")
    return twin


@router.get("/stats/{year}/{layer}")
def get_stat(year: int, layer: str) -> dict:
    stat = timeline_stat(year, layer)
    if stat is None:
        raise HTTPException(status_code=404, detail=f"{layer} {year} 无统计")
    return stat


@router.post("/query", response_model=QueryResponse)
def query_point(req: QueryRequest) -> QueryResponse:
    value = sample_query_grid(req.layer, req.year, req.lon, req.lat)
    return QueryResponse(
        layer=req.layer,
        label=layer_label(req.layer),
        year=req.year,
        lon=req.lon,
        lat=req.lat,
        value=value,
        explanation=_explain(req.layer, value),
    )
