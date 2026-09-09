from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any, Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 简易内存任务表，演示异步任务队列接口；生产可替换为 Celery / RQ / Redis。
_TASKS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


class TaskCreate(BaseModel):
    type: str
    payload: dict[str, Any] = {}


class TaskInfo(BaseModel):
    id: str
    type: str
    status: str
    created_at: str
    updated_at: str
    result: Any | None = None
    error: str | None = None


def _set(task_id: str, **kwargs: Any) -> None:
    with _LOCK:
        task = _TASKS.get(task_id, {})
        task.update(kwargs)
        task["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _TASKS[task_id] = task


def _run(task_id: str, runner: Callable[[dict[str, Any]], Any], payload: dict[str, Any]) -> None:
    _set(task_id, status="running")
    try:
        result = runner(payload)
        _set(task_id, status="succeeded", result=result)
    except Exception as exc:  # noqa: BLE001
        _set(task_id, status="failed", error=str(exc))


def _demo_runner(payload: dict[str, Any]) -> dict[str, Any]:
    """占位任务执行器：回显 payload。真实场景可在此触发报告生成 / 批量计算。"""
    return {"echo": payload, "message": "任务执行完成（占位实现）。"}


_RUNNERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "demo": _demo_runner,
}


@router.post("", response_model=TaskInfo)
def create_task(req: TaskCreate, background: BackgroundTasks) -> TaskInfo:
    runner = _RUNNERS.get(req.type)
    if runner is None:
        raise HTTPException(status_code=400, detail=f"未知任务类型：{req.type}")

    task_id = uuid.uuid4().hex
    now = datetime.now().isoformat(timespec="seconds")
    with _LOCK:
        _TASKS[task_id] = {
            "id": task_id,
            "type": req.type,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "result": None,
            "error": None,
        }
    background.add_task(_run, task_id, runner, req.payload)
    return TaskInfo(**_TASKS[task_id])


@router.get("/{task_id}", response_model=TaskInfo)
def get_task(task_id: str) -> TaskInfo:
    task = _TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskInfo(**task)
