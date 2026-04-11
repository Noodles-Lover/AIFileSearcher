from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.RAG.SystemManager import system
from backend.utils.settings_manager import settings_manager
from backend.utils.model_utils import list_local_embedding_models, list_local_llm_models

router = APIRouter()


@router.get("/api/embedding/list")
def get_embedding_models():
    return {
        "models": list_local_embedding_models(),
        "current_model": settings_manager.load().get("embedding_model", "bge-m3"),
    }


@router.get("/api/llm/list")
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
    max_new_tokens = request.get("max_new_tokens", 512)
    temperature = request.get("temperature", 0.7)
    top_p = request.get("top_p", 0.9)
    model_name = (request.get("model_name") or "").strip() or None

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        result = system.generate_with_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            model_name=model_name,
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
