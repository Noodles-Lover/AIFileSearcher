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
            "message": f"嵌入模型 [{model_name}] 加载成功",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/llm/list")
def get_llm_models():
    settings = settings_manager.load()
    sm = SystemManager.get_instance()
    return {
        "providers": ["local", "deepseek"],  # 可用的 LLM 提供商
        "models": list_local_llm_models(),    # 本地模型列表
        "current_provider": sm.current_llm_provider or settings.get("llm_provider", "local"),
        "current_model": sm.current_llm_name or settings.get("llm_model", ""),
        "has_api_key": bool(settings.get("deepseek_api_key")),
    }


@router.post("/api/llm/load")
def load_llm(request: Dict[str, Any]):
    provider = (request.get("provider") or "local").strip()
    model_name = (request.get("model_name") or "").strip()
    device = (request.get("device") or "").strip() or None

    try:
        sm = SystemManager.get_instance()
        
        if provider == "deepseek":
            # DeepSeek API 模式，不加载本地模型
            sm.reload_llm()  # 使用 settings 中的 api_key
            settings_manager.save({
                "llm_provider": "deepseek",
                "llm_model": model_name or "deepseek-chat",
            })
            return {
                "success": True,
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "status": "loaded",
                "message": "DeepSeek API 初始化成功",
            }
        else:
            # 本地模型模式
            if not model_name:
                raise HTTPException(status_code=400, detail="model_name is required for local LLM")
            
            sm.reload_llm(model_name=model_name)
            settings_manager.save({
                "llm_provider": "local",
                "llm_model": model_name,
            })
            return {
                "success": True,
                "provider": "local",
                "model_name": model_name,
                "status": "loaded",
                "message": f"本地 LLM 模型 [{model_name}] 加载成功",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/llm/config")
def config_llm(request: Dict[str, Any]):
    """配置 LLM 设置（provider、api_key 等）"""
    provider = (request.get("provider") or "local").strip()
    api_key = (request.get("api_key") or "").strip()
    model_name = (request.get("model_name") or "").strip()
    
    try:
        if provider == "deepseek":
            if not api_key:
                raise HTTPException(status_code=400, detail="DeepSeek API Key 不能为空")
            
            # 保存设置
            settings_manager.save({
                "llm_provider": "deepseek",
                "deepseek_api_key": api_key,
                "llm_model": model_name or "deepseek-chat",
            })
            
            # 初始化 DeepSeek
            sm = SystemManager.get_instance()
            sm.reload_llm()
            
            return {
                "success": True,
                "provider": "deepseek",
                "message": "DeepSeek API 配置成功",
            }
        else:
            # 本地模式
            settings_manager.save({
                "llm_provider": "local",
                "llm_model": model_name,
            })
            return {
                "success": True,
                "provider": "local",
                "message": "本地 LLM 配置成功",
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
