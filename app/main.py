from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.config import settings
from app.providers import OllamaProvider, ProviderError
from app.schemas import ErrorResponse, GenerateRequest, GenerateResponse, ModelsResponse

app = FastAPI(title=settings.app_name, version="0.1.0")
provider = OllamaProvider(base_url=settings.ollama_base_url, timeout_seconds=settings.request_timeout_seconds)


def require_internal_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    configured_key = settings.internal_api_key.strip()
    if not configured_key:
        return

    if x_api_key != configured_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "provider": settings.llm_provider}


@app.get("/v1/models", response_model=ModelsResponse, responses={502: {"model": ErrorResponse}})
async def list_models(_: Annotated[None, Depends(require_internal_api_key)]):
    try:
        models = await provider.list_models()
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return ModelsResponse(models=models)


@app.post(
    "/v1/generate",
    response_model=GenerateResponse,
    responses={401: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def generate(
    payload: GenerateRequest,
    _: Annotated[None, Depends(require_internal_api_key)],
):
    if not payload.messages and not payload.system_prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either messages or system_prompt is required")

    try:
        return await provider.generate(payload, default_model=settings.default_chat_model)
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
