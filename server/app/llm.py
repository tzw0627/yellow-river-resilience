from __future__ import annotations

from typing import Iterable

from .config import get_settings


class LLMNotConfigured(RuntimeError):
    pass


def _client(provider: str | None = None):
    settings = get_settings()
    config = settings.get_llm_config(provider)
    if not settings.llm_enabled_for(provider):
        raise LLMNotConfigured(f"未配置 {config['provider']} 的 API Key")
    from openai import OpenAI

    return OpenAI(api_key=config["api_key"], base_url=config["base_url"])


def chat_completion(messages: list[dict[str, str]], provider: str | None = None) -> str:
    """Call an OpenAI-compatible chat model and return its complete reply."""
    settings = get_settings()
    config = settings.get_llm_config(provider)
    client = _client(provider)
    response = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        temperature=settings.llm_temperature,
    )
    return response.choices[0].message.content or ""


def chat_completion_stream(
    messages: list[dict[str, str]], provider: str | None = None
) -> Iterable[str]:
    """Call an OpenAI-compatible model and yield incremental text deltas."""
    settings = get_settings()
    config = settings.get_llm_config(provider)
    client = _client(provider)
    stream = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        temperature=settings.llm_temperature,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


def rule_based_reply(user_text: str, context: str) -> str:
    """Fallback answer used when no provider API key is configured."""
    return (
        "（当前后端未配置大模型 API Key，以下为基于规则的占位回答。）\n\n"
        f"我已读取研究区当前图层与统计背景，针对你的问题“{user_text.strip()}”，"
        "建议结合左侧图层树切换 NDVI/EVI、四维生态韧性 ER 和洪水风险 FRI 图层对比观察。\n\n"
        "在 server/.env 中填写对应提供商的 API Key、Base URL 和模型后重启后端，即可获得真实大模型分析。"
    )
