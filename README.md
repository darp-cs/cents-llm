# Cents LLM Service

Cents LLM Service is a lightweight text-only gateway for all LLM calls in the Cents stack.

It is designed to be called by `cents-backend` so model providers can be swapped without
changing graph logic.

## Features

- FastAPI HTTP service for generation and model discovery
- Ollama provider adapter for local inference
- Optional internal API key protection (`X-API-Key`)
- Simple request/response contract for backend integration

## Local Setup

### Windows (native)

```powershell
scripts\setup.bat
scripts\start.bat
```

Alternative PowerShell scripts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

### macOS / Linux

```bash
chmod +x scripts/setup.sh scripts/start.sh
./scripts/setup.sh
./scripts/start.sh
```

## Environment

Copy `.env.example` to `.env` and adjust as needed.

Important variables:

- `INTERNAL_API_KEY` (optional)
- `OLLAMA_BASE_URL`
- `DEFAULT_CHAT_MODEL`
- `REQUEST_TIMEOUT_SECONDS`

## API

### Health

`GET /health`

### List models

`GET /v1/models`

### Generate text

`POST /v1/generate`

Request body:

```json
{
	"messages": [
		{ "role": "user", "content": "What is RAG?" }
	],
	"system_prompt": "You are a concise assistant.",
	"model": "qwen2.5:3b-instruct",
	"temperature": 0.3,
	"max_tokens": 512,
	"metadata": {
		"user_id": "...",
		"thread_id": "..."
	}
}
```

Response body:

```json
{
	"text": "RAG stands for retrieval-augmented generation...",
	"model": "qwen2.5:3b-instruct",
	"latency_ms": 432,
	"usage": {
		"prompt_tokens": 120,
		"completion_tokens": 78,
		"total_tokens": 198
	}
}
```

## Suggested Starter Models (RTX 3060 Ti, 8 GB VRAM)

Start with quantized instruct models:

- `qwen2.5:3b-instruct`
- `llama3.2:3b-instruct`
- `mistral:7b-instruct` (higher quality, higher latency/VRAM pressure)

Recommended defaults:

- `temperature`: `0.2` to `0.5`
- `max_tokens`: `256` to `512`
- Keep context small initially and increase after latency testing.