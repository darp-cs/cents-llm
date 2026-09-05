from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from app.config import settings
from app.model_catalog import ModelCatalog, ModelFolder
from app.providers import OllamaProvider, ProviderError
from app.schemas import (
    EmbeddingsRequest,
    EmbeddingsResponse,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    ModelFolderResponse,
    ModelsResponse,
)


def _configure_app_logging() -> None:
    app_logger = logging.getLogger("cents_llm")
    app_logger.setLevel(logging.INFO)

    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        app_logger.addHandler(handler)

    app_logger.propagate = False


_configure_app_logging()

app = FastAPI(title=settings.app_name, version="0.1.0")
provider = OllamaProvider(base_url=settings.ollama_base_url, timeout_seconds=settings.request_timeout_seconds)
catalog = ModelCatalog(settings.model_catalog_directory)


def require_internal_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    configured_key = settings.internal_api_key.strip()
    if not configured_key:
        return

    if x_api_key != configured_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    clean_value = value.strip()
    return clean_value if clean_value else None


def _list_available_folders() -> list[str]:
    return sorted(catalog.list_folders().keys())


def _get_folder_or_error(folder_name: str) -> ModelFolder:
    normalized_folder = ModelCatalog.normalize_folder_name(folder_name)
    if not normalized_folder:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="model_folder is required.")

    folder = catalog.get_folder(normalized_folder)
    if folder is None:
        available_folders = ", ".join(_list_available_folders()) or "none"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown model folder '{normalized_folder}'. "
                f"Available folders: {available_folders}."
            ),
        )

    return folder


def _resolve_default_model_from_folder(folder: ModelFolder) -> str:
    if folder.default_model:
        return folder.default_model

    if folder.models:
        return folder.models[0]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Model folder '{folder.name}' has no models configured.",
    )


def _resolve_generate_model(payload: GenerateRequest) -> str:
    folder = _get_folder_or_error(payload.model_folder)
    explicit_model = _clean_optional_text(payload.model)
    if explicit_model:
        return explicit_model

    return _resolve_default_model_from_folder(folder)


def _resolve_embedding_model(payload: EmbeddingsRequest) -> str:
    folder = _get_folder_or_error(payload.model_folder)
    explicit_model = _clean_optional_text(payload.model)
    if explicit_model:
        return explicit_model

    return _resolve_default_model_from_folder(folder)


def _to_embeddings_input_list(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return value


def _request_id_from_request(request: Request) -> str:
    request_id = request.headers.get("x-request-id", "")
    cleaned = request_id.strip()
    return cleaned if cleaned else "-"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "provider": settings.llm_provider}


@app.get("/v1/models", response_model=ModelsResponse, responses={502: {"model": ErrorResponse}})
async def list_models(request: Request, _: Annotated[None, Depends(require_internal_api_key)]):
    try:
        models = await provider.list_models(request_id=_request_id_from_request(request))
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    folder_map: dict[str, ModelFolderResponse] = {}
    for folder_name, folder in catalog.list_folders().items():
        folder_map[folder_name] = ModelFolderResponse(models=folder.models, default_model=folder.default_model)

    return ModelsResponse(models=models, folders=folder_map)


@app.post(
    "/v1/generate",
    response_model=GenerateResponse,
    responses={401: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def generate(
    payload: GenerateRequest,
    request: Request,
    _: Annotated[None, Depends(require_internal_api_key)],
):
    if not payload.messages and not payload.system_prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either messages or system_prompt is required")

    selected_model = _resolve_generate_model(payload)
    effective_payload = payload.model_copy(update={"model": selected_model})
    request_id = _request_id_from_request(request)

    try:
        return await provider.generate(effective_payload, request_id=request_id)
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@app.post(
    "/v1/embeddings",
    response_model=EmbeddingsResponse,
    responses={401: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def embeddings(
    payload: EmbeddingsRequest,
    request: Request,
    _: Annotated[None, Depends(require_internal_api_key)],
):
    selected_model = _resolve_embedding_model(payload)
    inputs = _to_embeddings_input_list(payload.input)
    request_id = _request_id_from_request(request)

    try:
        return await provider.embed(selected_model, inputs, metadata=payload.metadata, request_id=request_id)
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
