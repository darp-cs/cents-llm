# Cents LLM Service

Cents LLM Service is a lightweight text-only gateway for all LLM calls in the Cents stack.

It is designed to be called by `cents-backend` so model providers can be swapped without
changing graph logic.

## Features

- FastAPI HTTP service for generation and model discovery
- Ollama provider adapter for local inference
- Folder-based model catalog for routing by purpose (`text-generation`, `reasoning`, `embedding`, `multimodal`, `diffusion`, `speech`, `coding`)
- Embeddings endpoint for retrieval workflows
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

## Install Ollama

Install Ollama before starting this service.

### Windows

```powershell
winget install Ollama.Ollama
ollama --version
```

### macOS

```bash
brew install ollama
ollama --version
```

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

If Ollama is not already running:

```powershell
ollama serve
```

## Environment

Copy `.env.example` to `.env` and adjust as needed.

Important variables:

- `INTERNAL_API_KEY` (optional)
- `OLLAMA_BASE_URL`
- `MODEL_CATALOG_DIRECTORY` (folder manifests root, default `model_catalog`)
- `REQUEST_TIMEOUT_SECONDS`

## Model organization by folder

Use a folder manifest structure under `MODEL_CATALOG_DIRECTORY`.

Example structure:

```text
model_catalog/
├── text-generation/
│   └── models.json
├── reasoning/
│   └── models.json
├── embedding/
│   └── models.json
├── multimodal/
│   └── models.json
├── diffusion/
│   └── models.json
├── speech/
│   └── models.json
└── coding/
    └── models.json
```

Each folder supports either:

- `models.json` with object shape:

```json
{
	"default_model": "qwen2.5:3b-instruct",
	"models": [
		"qwen2.5:3b-instruct",
		"llama3.2:3b-instruct"
	]
}
```

- or `models.txt` + optional `default.txt`

### Default model per type

Each model type has its own default model in its folder manifest (`default_model`).
If a request only sends `model_folder` and omits `model`, the gateway uses that folder default.

| Model type folder | Current default model |
| --- | --- |
| `text-generation` | `qwen2.5:3b-instruct` |
| `reasoning` | `llama3.2:3b-instruct` |
| `embedding` | `nomic-embed-text` |
| `multimodal` | `llava:7b` |
| `diffusion` | `stable-diffusion-xl` |
| `speech` | `whisper:base` |
| `coding` | `qwen2.5-coder:3b` |

Important:

- These manifests are routing metadata only.
- Actual model weights are managed by Ollama (typically under `%USERPROFILE%\\.ollama\\models` on Windows).
- Pull models with Ollama first.
- Ollama does not physically store models inside the `model_catalog` folders. The folder mapping is logical routing, and the gateway picks models by `model_folder` and model name.

## Install models from model_catalog

You do not need to be in a specific folder to pull models. `ollama pull` works from any terminal location.

Command pattern:

```powershell
ollama pull <model-name>
```

Pull one default model per type:

```powershell
ollama pull qwen2.5:3b-instruct
ollama pull llama3.2:3b-instruct
ollama pull nomic-embed-text
ollama pull llava:7b
ollama pull stable-diffusion-xl
ollama pull whisper:base
ollama pull qwen2.5-coder:3b
```

Verify installed models:

```powershell
ollama list
```

Optional quick test:

```powershell
ollama run qwen2.5:3b-instruct
```

## How local execution works

1. `ollama pull ...` downloads model weights to your local Ollama store.
2. `cents-llm` calls your local Ollama API at `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`).
3. Ollama runs inference locally and uses your local GPU automatically when supported and available.
4. Model type folders in `model_catalog` are routing metadata only; they do not contain model weight files.

## How requests resolve model selection

1. Backend sends `model_folder` (required) and optional `model`.
2. `cents-llm` resolves the model as:
	1. use explicit `model` if provided
	2. otherwise use `default_model` from the requested `model_folder`
3. `cents-llm` calls Ollama:
	1. `POST /api/chat` for text generation
	2. `POST /api/embed` for embeddings

## API

### Health

`GET /health`

### List models

`GET /v1/models`

Response now includes both a flat installed model list and folder groupings from the catalog.

### Generate text

`POST /v1/generate`

Request body:

```json
{
	"messages": [
		{ "role": "user", "content": "What is RAG?" }
	],
	"system_prompt": "You are a concise assistant.",
	"model_folder": "reasoning",
	"model": "qwen2.5:3b-instruct",
	"temperature": 0.3,
	"max_tokens": 512,
	"metadata": {
		"user_id": "...",
		"thread_id": "..."
	}
}
```

Model selection precedence for `POST /v1/generate`:

1. `model` (if provided)
2. `model_folder` default model (`default_model` in that folder)

`model_folder` is required for `POST /v1/generate`.

### Create embeddings

`POST /v1/embeddings`

Request body:

```json
{
	"input": "What is retrieval augmented generation?",
	"model_folder": "embedding"
}
```

Response body:

```json
{
	"embeddings": [[0.01, -0.22, 0.44]],
	"model": "nomic-embed-text",
	"dimensions": 768
}
```

Model selection precedence for `POST /v1/embeddings`:

1. `model` (if provided)
2. `model_folder` default model (`default_model` in that folder)

`model_folder` is required for `POST /v1/embeddings`.

## Suggested Starter Models (RTX 3060 Ti, 8 GB VRAM)

Start with quantized instruct models:

- `qwen2.5:3b-instruct`
- `llama3.2:3b-instruct`
- `mistral:7b-instruct` (higher quality, higher latency/VRAM pressure)

Recommended defaults:

- `temperature`: `0.2` to `0.5`
- `max_tokens`: `256` to `512`
- Keep context small initially and increase after latency testing.