import asyncio
import json
import threading
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.RAG.SystemManager import SystemManager
from backend.utils.settings_manager import settings_manager
from backend.utils.model_utils import list_local_embedding_models, list_local_llm_models

router = APIRouter()


@router.get("/api/embedding/list")
def get_embedding_models():
    settings = settings_manager.load()
    current_model = settings.get("embedding_model", "")
    # 如果当前模型不在本地模型列表中，返回空字符串
    local_models = list_local_embedding_models()
    if current_model and current_model not in local_models:
        current_model = ""
    return {
        "models": local_models,
        "current_model": current_model,
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
async def load_llm(request: Dict[str, Any]):
    """加载 LLM 模型（SSE 进度反馈）

    body 可为空：provider/model_name 缺省时按 settings 配置加载（前端启动自动触发）。
    force=True 时强制重载（设置页手动切换模型）。
    """
    provider = (request.get("provider") or "").strip()
    model_name = (request.get("model_name") or "").strip()
    force = bool(request.get("force", False))

    async def event_generator():
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def progress_cb(item: Dict[str, Any]):
            loop.call_soon_threadsafe(queue.put_nowait, item)

        def _run():
            try:
                sm = SystemManager.get_instance()
                if not provider:
                    provider_eff = settings_manager.load().get("llm_provider", "local")
                else:
                    provider_eff = provider

                if provider_eff == "deepseek":
                    progress_cb({"status": "loading", "stage": "api", "msg": "正在初始化 DeepSeek API..."})
                    sm.load_llm(force=True, progress_cb=progress_cb)
                    settings_manager.save({
                        "llm_provider": "deepseek",
                        "llm_model": model_name or "deepseek-chat",
                    })
                else:
                    if not model_name:
                        model_name_eff = settings_manager.load().get("llm_model", "")
                    else:
                        model_name_eff = model_name
                    if not model_name_eff:
                        raise ValueError("未配置本地 LLM 模型，请在设置中选择")
                    llm = sm.load_llm(model_name=model_name_eff, force=force, progress_cb=progress_cb)
                    if llm is None:
                        raise ValueError("LLM 模型加载失败")
                    settings_manager.save({
                        "llm_provider": "local",
                        "llm_model": model_name_eff,
                    })
                progress_cb({"status": "complete", "msg": "模型加载完成"})
            except Exception as e:
                progress_cb({"status": "error", "msg": str(e)})

        threading.Thread(target=_run, name="llm-load", daemon=True).start()

        while True:
            item = await queue.get()
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)
            if item.get("status") in ("complete", "error"):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "X-Accel-Buffering": "no"
        }
    )


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
