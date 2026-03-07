from fastapi import APIRouter, HTTPException, Query
from api.everything import EverythingClient

router = APIRouter()

# 初始化 Everything 客户端
client = EverythingClient()

@router.get("/api/search")
def search_files(q: str = "", count: int = 100, parent_path: str = None):
    """
    搜索文件
    """
    query = q
    if parent_path:
        # 如果提供了父目錄，限制在該目錄下搜索
        query = f'parent:"{parent_path}" {q}'.strip()
    
    results = client.search(query, count=count)
    
    if results == "CONNECTION_ERROR":
         raise HTTPException(
             status_code=503, 
             detail="無法連接到 Everything 伺服器。請確保 Everything 正在運行並已啟用 HTTP 伺服器（工具 -> 選項 -> HTTP 伺服器）。"
         )
        
    return {"results": results}

@router.get("/api/list")
def list_files(path: str):
    """
    列出指定目錄下的文件
    """
    results = client.get_files_in_folder(path)
    
    if results == "CONNECTION_ERROR":
        raise HTTPException(
            status_code=503, 
            detail="無法連接到 Everything 伺服器。請確保 Everything 正在運行並已啟用 HTTP 伺服器。"
        )
        
    return {"results": results}
