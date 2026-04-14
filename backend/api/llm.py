from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.RAG.SystemManager import SystemManager
from backend.utils.settings_manager import settings_manager
from backend.utils.model_utils import list_local_embedding_models, list_local_llm_models

router = APIRouter()


@router.get("/api/embedding/list")
def get_embedding_models():
    return {
        "models": list_local_embedding_models(),
        "current_model": settings_manager.load().get("embedding_model", "bge-m3"),
    }


@router.post("/api/embedding/load")
def load_embedding_model(request: Dict[str, Any]):
    model_name = (request.get("model_name") or "").strip()

    if not model_name:
        raise HTTPException(status_code=400, detail="model_name is required")

    try:
        sm = SystemManager.get_instance()
        sm.reload_embedding_model(model_name=model_name)
        settings_manager.save({"embedding_model": model_name})
        return {
            "success": True,
            "model_name": model_name,
            "status": "loaded",
            "message": f"✅ 嵌入模型 [{model_name}] 加载成功",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/llm/list")
def get_llm_models():
    sm = SystemManager.get_instance()
    return {
        "models": list_local_llm_models(),
        "current_model": sm.current_llm_name or settings_manager.load().get("llm_model", ""),
    }


@router.post("/api/llm/load")
def load_llm(request: Dict[str, Any]):
    model_name = (request.get("model_name") or "").strip()
    device = (request.get("device") or "").strip() or None

    if not model_name:
        raise HTTPException(status_code=400, detail="model_name is required")

    try:
        sm = SystemManager.get_instance()
        sm.reload_llm(model_name=model_name)
        settings_manager.save({"llm_model": model_name})
        return {
            "success": True,
            "model_name": model_name,
            "status": "loaded",
            "message": f"✅ LLM 模型 [{model_name}] 加载成功",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/llm/unload")
def unload_llm():
    sm = SystemManager.get_instance()
    sm.unload_llm()
    return {"success": True, "message": "LLM 已卸载"}


@router.post("/api/llm/generate")
def generate_text(request: Dict[str, Any]):
    prompt = (request.get("prompt") or "").strip()
    system_prompt = (request.get("system_prompt") or "").strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        sm = SystemManager.get_instance()
        result = sm.generate_with_llm(prompt=prompt, system_prompt=system_prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
