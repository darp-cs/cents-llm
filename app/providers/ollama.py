from __future__ import annotations

import time

import httpx

from app.schemas import GenerateRequest, GenerateResponse, Usage


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    def __init__(self, base_url: str, timeout_seconds: int):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                response = await client.get("/api/tags")
        except httpx.RequestError as exc:
            raise ProviderError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc

        if response.status_code >= 400:
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

        return models

    async def generate(self, request: GenerateRequest, default_model: str) -> GenerateResponse:
        selected_model = request.model or default_model

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
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds) as client:
                response = await client.post("/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderError("Ollama generation request timed out.") from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderError(
                f"Ollama generation request failed with status {response.status_code}: {response.text}"
            )

        response_payload = response.json()
        message = response_payload.get("message") if isinstance(response_payload, dict) else None
        text = message.get("content", "") if isinstance(message, dict) else ""

        generated_text = str(text).strip()
        if not generated_text:
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

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return GenerateResponse(text=generated_text, model=selected_model, latency_ms=latency_ms, usage=usage)
