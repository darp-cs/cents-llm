from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.schemas import EmbeddingsResponse, GenerateRequest, GenerateResponse, Usage


class ProviderError(RuntimeError):
    pass


logger = logging.getLogger("cents_llm.provider.ollama")


class OllamaProvider:
    def __init__(self, base_url: str, timeout_seconds: int):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def list_models(self, request_id: str | None = None) -> list[str]:
        started_at = time.perf_counter()
        log_request_id = request_id or "-"

        logger.info("ollama.list_models.start request_id=%s", log_request_id)
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                response = await client.get("/api/tags")
        except httpx.RequestError as exc:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.exception(
                "ollama.list_models.error request_id=%s elapsed_ms=%s base_url=%s",
                log_request_id,
                elapsed_ms,
                self.base_url,
            )
            raise ProviderError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc

        if response.status_code >= 400:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.error(
                "ollama.list_models.http_error request_id=%s status_code=%s elapsed_ms=%s body=%s",
                log_request_id,
                response.status_code,
                elapsed_ms,
                self._truncate_for_log(response.text),
            )
            raise ProviderError(
                f"Ollama list models request failed with status {response.status_code}: {response.text}"
            )

        payload = response.json()
        raw_models = payload.get("models", [])
        models: list[str] = []

        for model_entry in raw_models:
            if isinstance(model_entry, dict):
                name = model_entry.get("name")
                if isinstance(name, str) and name.strip():
                    models.append(name.strip())

        elapsed_ms = self._elapsed_ms(started_at)
        logger.info(
            "ollama.list_models.success request_id=%s model_count=%s elapsed_ms=%s",
            log_request_id,
            len(models),
            elapsed_ms,
        )
        return models

    async def generate(self, request: GenerateRequest, request_id: str | None = None) -> GenerateResponse:
        selected_model = str(request.model).strip() if request.model else ""
        if not selected_model:
            raise ProviderError("A model must be selected before calling the provider.")

        log_request_id = request_id or self._metadata_request_id(request.metadata)

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        messages.extend([{"role": m.role, "content": m.content} for m in request.messages])

        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        started_at = time.perf_counter()
        logger.info(
            "ollama.generate.start request_id=%s model=%s message_count=%s has_system_prompt=%s max_tokens=%s temperature=%s",
            log_request_id,
            selected_model,
            len(request.messages),
            bool(request.system_prompt),
            request.max_tokens,
            request.temperature,
        )

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                response = await client.post("/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.exception(
                "ollama.generate.timeout request_id=%s model=%s elapsed_ms=%s",
                log_request_id,
                selected_model,
                elapsed_ms,
            )
            raise ProviderError("Ollama generation request timed out.") from exc
        except httpx.RequestError as exc:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.exception(
                "ollama.generate.error request_id=%s model=%s elapsed_ms=%s base_url=%s",
                log_request_id,
                selected_model,
                elapsed_ms,
                self.base_url,
            )
            raise ProviderError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc

        if response.status_code >= 400:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.error(
                "ollama.generate.http_error request_id=%s model=%s status_code=%s elapsed_ms=%s body=%s",
                log_request_id,
                selected_model,
                response.status_code,
                elapsed_ms,
                self._truncate_for_log(response.text),
            )
            raise ProviderError(
                f"Ollama generation request failed with status {response.status_code}: {response.text}"
            )

        response_payload = response.json()
        message = response_payload.get("message") if isinstance(response_payload, dict) else None
        text = message.get("content", "") if isinstance(message, dict) else ""

        generated_text = str(text).strip()
        if not generated_text:
            logger.error(
                "ollama.generate.empty_response request_id=%s model=%s",
                log_request_id,
                selected_model,
            )
            raise ProviderError("Ollama returned an empty response.")

        prompt_tokens = response_payload.get("prompt_eval_count")
        completion_tokens = response_payload.get("eval_count")

        usage = Usage(
            prompt_tokens=prompt_tokens if isinstance(prompt_tokens, int) else None,
            completion_tokens=completion_tokens if isinstance(completion_tokens, int) else None,
            total_tokens=(prompt_tokens + completion_tokens)
            if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int)
            else None,
        )

        latency_ms = self._elapsed_ms(started_at)
        logger.info(
            "ollama.generate.success request_id=%s model=%s latency_ms=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            log_request_id,
            selected_model,
            latency_ms,
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )
        return GenerateResponse(text=generated_text, model=selected_model, latency_ms=latency_ms, usage=usage)

    async def embed(
        self,
        model: str,
        inputs: list[str],
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> EmbeddingsResponse:
        payload = {
            "model": model,
            "input": inputs if len(inputs) > 1 else inputs[0],
        }

        started_at = time.perf_counter()
        log_request_id = request_id or self._metadata_request_id(metadata)
        logger.info(
            "ollama.embed.start request_id=%s model=%s input_count=%s",
            log_request_id,
            model,
            len(inputs),
        )

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                response = await client.post("/api/embed", json=payload)
        except httpx.TimeoutException as exc:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.exception(
                "ollama.embed.timeout request_id=%s model=%s elapsed_ms=%s",
                log_request_id,
                model,
                elapsed_ms,
            )
            raise ProviderError("Ollama embedding request timed out.") from exc
        except httpx.RequestError as exc:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.exception(
                "ollama.embed.error request_id=%s model=%s elapsed_ms=%s base_url=%s",
                log_request_id,
                model,
                elapsed_ms,
                self.base_url,
            )
            raise ProviderError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc

        if response.status_code >= 400:
            elapsed_ms = self._elapsed_ms(started_at)
            logger.error(
                "ollama.embed.http_error request_id=%s model=%s status_code=%s elapsed_ms=%s body=%s",
                log_request_id,
                model,
                response.status_code,
                elapsed_ms,
                self._truncate_for_log(response.text),
            )
            raise ProviderError(
                f"Ollama embedding request failed with status {response.status_code}: {response.text}"
            )

        response_payload = response.json()
        embeddings = self._extract_embeddings(response_payload)
        if not embeddings:
            logger.error(
                "ollama.embed.empty_response request_id=%s model=%s",
                log_request_id,
                model,
            )
            raise ProviderError("Ollama returned an empty embedding response.")

        if len(embeddings) != len(inputs):
            logger.error(
                "ollama.embed.size_mismatch request_id=%s model=%s input_count=%s embedding_count=%s",
                log_request_id,
                model,
                len(inputs),
                len(embeddings),
            )
            raise ProviderError(
                "Ollama embedding response size did not match the number of input items."
            )

        first_dimension = len(embeddings[0]) if embeddings and embeddings[0] else 0
        dimensions = first_dimension if first_dimension > 0 else None
        elapsed_ms = self._elapsed_ms(started_at)
        logger.info(
            "ollama.embed.success request_id=%s model=%s input_count=%s dimensions=%s elapsed_ms=%s",
            log_request_id,
            model,
            len(inputs),
            dimensions,
            elapsed_ms,
        )
        return EmbeddingsResponse(embeddings=embeddings, model=model, dimensions=dimensions)

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)

    @staticmethod
    def _truncate_for_log(value: str, max_length: int = 500) -> str:
        if len(value) <= max_length:
            return value
        return f"{value[:max_length]}..."

    @staticmethod
    def _metadata_request_id(metadata: dict[str, Any] | None) -> str:
        if not isinstance(metadata, dict):
            return "-"

        request_id = metadata.get("request_id")
        if not isinstance(request_id, str):
            return "-"

        cleaned = request_id.strip()
        return cleaned if cleaned else "-"

    @staticmethod
    def _extract_embeddings(payload: Any) -> list[list[float]]:
        if not isinstance(payload, dict):
            return []

        raw_embeddings = payload.get("embeddings")
        if isinstance(raw_embeddings, list):
            normalized: list[list[float]] = []
            for embedding in raw_embeddings:
                vector = OllamaProvider._normalize_embedding_vector(embedding)
                if vector:
                    normalized.append(vector)
            if normalized:
                return normalized

        vector = OllamaProvider._normalize_embedding_vector(payload.get("embedding"))
        return [vector] if vector else []

    @staticmethod
    def _normalize_embedding_vector(value: Any) -> list[float]:
        if not isinstance(value, list):
            return []

        normalized: list[float] = []
        for entry in value:
            if isinstance(entry, bool):
                return []
            if not isinstance(entry, (int, float)):
                return []
            normalized.append(float(entry))

        return normalized
