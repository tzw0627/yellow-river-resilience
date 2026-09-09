from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import agent, data, report, tasks

settings = get_settings()

app = FastAPI(
    title="黄河滩区生态韧性数智平台 API",
    version="0.1.0",
    description="数据查询、智能体问答、报告生成与任务接口。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(agent.router)
app.include_router(report.router)
app.include_router(tasks.router)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.normalize_llm_provider(settings.llm_provider),
        "llm_enabled": settings.llm_enabled,
        "data_dir": str(settings.data_path),
        "data_dir_exists": settings.data_path.exists(),
    }


# 静态数据：把 frontend/data 暴露到 /data，前端 overlay/查询网格/边界沿用相对路径。
if settings.data_path.exists():
    app.mount("/data", StaticFiles(directory=str(settings.data_path)), name="data")

# 生产环境：若配置了 web/dist，则由后端直接托管打包后的前端。
web_dist = settings.web_dist_path
if web_dist is not None:
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="web")
