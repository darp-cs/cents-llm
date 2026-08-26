from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class GenerateRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    system_prompt: str | None = None
    model: str | None = None
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    metadata: dict[str, Any] | None = None


class Usage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class GenerateResponse(BaseModel):
    text: str
    model: str
    latency_ms: int
    usage: Usage = Field(default_factory=Usage)


class ModelsResponse(BaseModel):
    models: list[str]


class ErrorResponse(BaseModel):
    detail: str
