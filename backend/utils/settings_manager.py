import json
import os
from typing import Any, Dict

from .path_utils import get_data_path


DEFAULT_SETTINGS: Dict[str, Any] = {
    "include_subfolders": False,
    "embedding_model": "bge-m3",
    "llm_provider": "local",  # "local" 或 "deepseek"
    "llm_model": "",          # 本地模型名称
    "deepseek_api_key": "",   # DeepSeek API Key
    "query_rewrite_enabled": False,
    "index_type": "IndexFlatL2",
}


class SettingsManager:
    def __init__(self):
        self.file_path = get_data_path("settings.json")

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            return self.save(DEFAULT_SETTINGS)

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            return self.save(DEFAULT_SETTINGS)

        normalized_settings = dict(raw_settings)

        if "recursive_folder_listing" in normalized_settings and "include_subfolders" not in normalized_settings:
            normalized_settings["include_subfolders"] = bool(normalized_settings["recursive_folder_listing"])

        return {**DEFAULT_SETTINGS, **normalized_settings}

    def save(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        merged_settings = {**DEFAULT_SETTINGS, **settings}
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(merged_settings, f, ensure_ascii=False, indent=2)
        return merged_settings


settings_manager = SettingsManager()
