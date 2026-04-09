import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from backend.RAG.SystemManager import system
from backend.utils.path_utils import get_models_path
from backend.utils.settings_manager import settings_manager

router = APIRouter()


def list_local_llm_models() -> List[str]:
    models_root = get_models_path()
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


@router.get("/api/llm/models")
def get_llm_models():
    return {
        "models": list_local_llm_models(),
        "current_model": system.current_llm_name or settings_manager.load().get("llm_model", ""),
    }


@router.post("/api/llm/load")
def load_llm(request: Dict[str, Any]):
    model_name = (request.get("model_name") or "").strip()
    device = (request.get("device") or "").strip() or None

    if not model_name:
        raise HTTPException(status_code=400, detail="model_name is required")

    try:
        system.load_local_llm(model_name=model_name, device=device)
        settings_manager.save({"llm_model": model_name})
        return {
            "success": True,
            "model_name": model_name,
            "device": device or "auto",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/llm/unload")
def unload_llm():
    system.unload_local_llm()
    return {"success": True}


@router.post("/api/llm/generate")
def generate_text(request: Dict[str, Any]):
    prompt = (request.get("prompt") or "").strip()
    system_prompt = (request.get("system_prompt") or "").strip()
    model_name = (request.get("model_name") or "").strip() or None
    device = (request.get("device") or "").strip() or None
    max_new_tokens = int(request.get("max_new_tokens", 512))
    temperature = float(request.get("temperature", 0.7))
    top_p = float(request.get("top_p", 0.9))

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        output = system.generate_with_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            model_name=model_name,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            device=device,
        )
        return {
            "success": True,
            "output": output,
            "model_name": system.current_llm_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
