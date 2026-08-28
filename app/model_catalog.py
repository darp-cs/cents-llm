from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelFolder:
    name: str
    models: list[str]
    default_model: str | None


class ModelCatalog:
    def __init__(self, root_directory: str):
        self.root_directory = Path(root_directory)

    @staticmethod
    def normalize_folder_name(name: str | None) -> str | None:
        if not name:
            return None
        normalized = name.strip().lower()
        return normalized or None

    def list_folders(self) -> dict[str, ModelFolder]:
        if not self.root_directory.exists() or not self.root_directory.is_dir():
            return {}

        folders: dict[str, ModelFolder] = {}
        for entry in sorted(self.root_directory.iterdir(), key=lambda path: path.name.lower()):
            if not entry.is_dir():
                continue

            folder_name = self.normalize_folder_name(entry.name)
            if not folder_name:
                continue

            models, default_model = self._load_folder(entry)
            folders[folder_name] = ModelFolder(name=folder_name, models=models, default_model=default_model)

        return folders

    def get_folder(self, folder_name: str | None) -> ModelFolder | None:
        normalized = self.normalize_folder_name(folder_name)
        if not normalized:
            return None

        folders = self.list_folders()
        return folders.get(normalized)

    def resolve_model(self, folder_name: str | None) -> str | None:
        folder = self.get_folder(folder_name)
        if folder is None:
            return None

        if folder.default_model:
            return folder.default_model

        if folder.models:
            return folder.models[0]

        return None

    @staticmethod
    def _normalize_model_names(raw_models: list[Any]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for value in raw_models:
            model_name = str(value).strip()
            if not model_name or model_name in seen:
                continue

            normalized.append(model_name)
            seen.add(model_name)

        return normalized

    @staticmethod
    def _read_non_empty_lines(path: Path) -> list[str]:
        if not path.exists() or not path.is_file():
            return []

        values: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#"):
                continue
            values.append(clean_line)

        return values

    def _load_folder(self, folder_path: Path) -> tuple[list[str], str | None]:
        json_manifest_path = folder_path / "models.json"
        if json_manifest_path.exists() and json_manifest_path.is_file():
            models, default_model = self._load_json_manifest(json_manifest_path)
            return models, default_model

        models = self._normalize_model_names(self._read_non_empty_lines(folder_path / "models.txt"))
        default_lines = self._read_non_empty_lines(folder_path / "default.txt")
        default_model = default_lines[0].strip() if default_lines else None

        if default_model and default_model not in models:
            models.insert(0, default_model)

        return models, default_model

    def _load_json_manifest(self, path: Path) -> tuple[list[str], str | None]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return [], None

        if isinstance(payload, list):
            return self._normalize_model_names(payload), None

        if not isinstance(payload, dict):
            return [], None

        raw_models = payload.get("models", [])
        models = self._normalize_model_names(raw_models if isinstance(raw_models, list) else [])

        raw_default_model = payload.get("default_model")
        default_model = str(raw_default_model).strip() if isinstance(raw_default_model, str) else None
        if default_model and default_model not in models:
            models.insert(0, default_model)

        return models, default_model
