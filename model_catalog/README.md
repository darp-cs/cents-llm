# Model Catalog

This directory stores model routing manifests by purpose.

- `text-generation/models.json`: default general chat generation models
- `reasoning/models.json`: stronger reasoning and judge-oriented models
- `embedding/models.json`: embedding models used for retrieval vectors
- `multimodal/models.json`: vision-language or other multimodal models
- `diffusion/models.json`: image generation models
- `speech/models.json`: speech-to-text or text-to-speech models
- `coding/models.json`: code-focused models

Defaults stay under ~6 GB VRAM so they fit comfortably on a 12 GB GPU (two can be resident
at once). The rest of each `models` list is ordered smallest-to-largest and capped at roughly
20 GB, which is the practical ceiling once you offload part of a larger model to system RAM.

Every entry in `text-generation`, `reasoning`, `coding`, `embedding`, and `multimodal` is an
Ollama library tag and can be pulled directly.

These files do not contain model weights. Pull weights with Ollama:

```powershell
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull qwen3:8b-q4_K_M
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
ollama pull minicpm-v:8b-2.6-q4_0
ollama pull bge-m3
```

Ollama does not host diffusion or speech models, so `diffusion/models.json` and
`speech/models.json` remain routing hints for external backends.

Manifest object format:

```json
{
  "default_model": "model-name",
  "models": ["model-name", "other-model"]
}
```
