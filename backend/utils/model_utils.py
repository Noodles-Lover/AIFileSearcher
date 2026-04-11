import os
from typing import List

from backend.utils.path_utils import get_embedding_models_path, get_llm_models_path


def list_local_embedding_models() -> List[str]:
    models_root = get_embedding_models_path()
    if not os.path.exists(models_root):
        return []

    candidates: List[str] = []
    for item in os.listdir(models_root):
        model_dir = os.path.join(models_root, item)
        if not os.path.isdir(model_dir):
            continue

        config_path = os.path.join(model_dir, "config.json")
        config_st_path = os.path.join(model_dir, "config_sentence_transformers.json")
        if not os.path.exists(config_path) and not os.path.exists(config_st_path):
            continue

        has_weights = False
        for root, _, files in os.walk(model_dir):
            for filename in files:
                lower_name = filename.lower()
                if (
                    lower_name.endswith(".safetensors")
                    or lower_name == "pytorch_model.bin"
                    or lower_name == "model.safetensors.index.json"
                    or lower_name == "pytorch_model.bin.index.json"
                    or lower_name.endswith(".onnx")
                ):
                    has_weights = True
                    break
            if has_weights:
                break

        if has_weights:
            candidates.append(item)

    return sorted(candidates, key=str.lower)


def list_local_llm_models() -> List[str]:
    models_root = get_llm_models_path()
    if not os.path.exists(models_root):
        return []

    candidates: List[str] = []
    for item in os.listdir(models_root):
        model_dir = os.path.join(models_root, item)
        if not os.path.isdir(model_dir):
            continue

        config_path = os.path.join(model_dir, "config.json")
        if not os.path.exists(config_path):
            continue

        has_weights = False
        for root, _, files in os.walk(model_dir):
            for filename in files:
                lower_name = filename.lower()
                if (
                    lower_name.endswith(".safetensors")
                    or lower_name == "pytorch_model.bin"
                    or lower_name == "model.safetensors.index.json"
                    or lower_name == "pytorch_model.bin.index.json"
                ):
                    has_weights = True
                    break
            if has_weights:
                break

        if has_weights:
            candidates.append(item)

    return sorted(candidates, key=str.lower)
