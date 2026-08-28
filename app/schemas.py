from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(default_factory=list)
    system_prompt: str | None = None
    model: str | None = None
    model_folder: str = Field(min_length=1)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    metadata: dict[str, Any] | None = None


class EmbeddingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: str | list[str]
    model: str | None = None
    model_folder: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None

    @field_validator("input")
    @classmethod
    def validate_input(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            clean_text = value.strip()
            if not clean_text:
                raise ValueError("input must be a non-empty string")
            return clean_text

        normalized = [str(item).strip() for item in value if str(item).strip()]
        if not normalized:
            raise ValueError("input must include at least one non-empty string")
        return normalized


class Usage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class GenerateResponse(BaseModel):
    text: str
    model: str
    latency_ms: int
    usage: Usage = Field(default_factory=Usage)


class EmbeddingsResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int | None = None


class ModelFolderResponse(BaseModel):
    models: list[str]
    default_model: str | None = None


class ModelsResponse(BaseModel):
    models: list[str]
    folders: dict[str, ModelFolderResponse] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    detail: str
