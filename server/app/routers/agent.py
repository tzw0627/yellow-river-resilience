from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agent_logic import (
    buildAgentAnswer,
    buildAgentContext,
    buildAgentMessages,
    classifyIntent,
    getLocalStats,
)
from ..config import get_settings
from ..llm import LLMNotConfigured, chat_completion, chat_completion_stream
from ..rag import rag_status

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    year: int | None = None
    layer: str | None = None
    regionId: str | None = None
    query: dict | None = None
    provider: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    llm_enabled: bool
    model: str | None = None


class RagSearchResponse(BaseModel):
    context: str
    status: dict


def _last_user(req: ChatRequest) -> str:
    return next((m.content for m in reversed(req.messages) if m.role == "user"), "")


def _agent_state(req: ChatRequest) -> tuple[str, str, dict, list[dict]]:
    question = _last_user(req)
    intent = classifyIntent(question)
    context = buildAgentContext(intent, question, req.year, req.layer, req.regionId, req.query)
    stats = getLocalStats(question, req.year, req.layer)
    return question, intent, context, stats


def _messages_for_llm(req: ChatRequest, question: str, context: dict) -> list[dict[str, str]]:
    history = [{"role": m.role, "content": m.content} for m in req.messages]
    return buildAgentMessages(question, context, history)


def _provider(req: ChatRequest) -> str:
    return get_settings().normalize_llm_provider(req.provider)


def _fallback(req: ChatRequest) -> str:
    question, intent, context, stats = _agent_state(req)
    return buildAgentAnswer(intent, question, context, stats)


@router.get("/status")
def status() -> dict:
    settings = get_settings()
    active_provider = settings.normalize_llm_provider(settings.llm_provider)
    active_config = settings.get_llm_config(active_provider)
    active_enabled = settings.llm_enabled_for(active_provider)
    return {
        "provider": active_provider,
        "llm_enabled": active_enabled,
        "model": active_config["model"] if active_enabled else None,
        "base_url": active_config["base_url"] if active_enabled else None,
        "providers": settings.llm_provider_options(),
        "rag": rag_status(),
    }


@router.post("/rag/context", response_model=RagSearchResponse)
def rag_context(req: ChatRequest) -> RagSearchResponse:
    question, _, context, _ = _agent_state(req)
    prompt_context = buildAgentMessages(question, context, [])[0]["content"]
    return RagSearchResponse(context=prompt_context, status=rag_status())


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    settings = get_settings()
    provider = _provider(req)
    config = settings.get_llm_config(provider)
    enabled = settings.llm_enabled_for(provider)
    question, intent, context, stats = _agent_state(req)

    if intent != "general_chat" or not enabled:
        return ChatResponse(
            reply=buildAgentAnswer(intent, question, context, stats),
            llm_enabled=enabled,
            model=config["model"] if enabled else None,
        )

    try:
        model_reply = chat_completion(_messages_for_llm(req, question, context), provider)
        reply = buildAgentAnswer(intent, question, context, stats, model_reply=model_reply)
        return ChatResponse(reply=reply, llm_enabled=True, model=config["model"])
    except LLMNotConfigured:
        return ChatResponse(reply=buildAgentAnswer(intent, question, context, stats), llm_enabled=False)
    except Exception:  # noqa: BLE001
        return ChatResponse(reply=buildAgentAnswer(intent, question, context, stats), llm_enabled=False)


@router.post("/chat/stream")
def chat_stream(req: ChatRequest):
    settings = get_settings()
    provider = _provider(req)
    enabled = settings.llm_enabled_for(provider)
    question, intent, context, stats = _agent_state(req)

    if intent != "general_chat" or not enabled:
        text = buildAgentAnswer(intent, question, context, stats)

        def fallback_stream():
            yield text

        return StreamingResponse(fallback_stream(), media_type="text/plain; charset=utf-8")

    def generate():
        try:
            for piece in chat_completion_stream(_messages_for_llm(req, question, context), provider):
                yield piece
        except LLMNotConfigured:
            yield buildAgentAnswer(intent, question, context, stats)
        except Exception as exc:  # noqa: BLE001
            fallback = buildAgentAnswer(intent, question, context, stats)
            yield f"{fallback}\n\n（模型调用失败，已使用本地规则兜底：{exc}）"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
