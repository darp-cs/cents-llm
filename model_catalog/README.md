# Model Catalog

This directory stores model routing manifests by purpose.

- `text-generation/models.json`: default general chat generation models
- `reasoning/models.json`: stronger reasoning and judge-oriented models
- `embedding/models.json`: embedding models used for retrieval vectors
- `multimodal/models.json`: vision-language or other multimodal models
- `diffusion/models.json`: image generation models
- `speech/models.json`: speech-to-text or text-to-speech models
- `coding/models.json`: code-focused models

These files do not contain model weights. Pull weights with Ollama:

```powershell
ollama pull qwen2.5:3b-instruct
ollama pull llama3.2:3b-instruct
ollama pull nomic-embed-text
```

Manifest object format:

```json
{
  "default_model": "model-name",
  "models": ["model-name", "other-model"]
}
```
