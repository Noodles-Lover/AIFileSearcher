import sys
import os
import time

from backend.utils.path_utils import ensure_project_path

# 确保项目根目录在路径中
ensure_project_path()

from fastapi import APIRouter, HTTPException, Query
from api.everything import EverythingClient
from backend.RAG.SystemManager import system

router = APIRouter()

# 初始化 Everything 客户端
client = EverythingClient()

@router.get("/api/search")
def search_files(q: str = "", count: int = 100, parent_path: str = None):
    """
    搜索文件 (基於 Everything)
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
def list_files(parent_path: str = ""):
    """
    列出指定目錄下的文件
    """
    try:
        # 首先尝试使用 Everything
        results = client.get_files_in_folder(parent_path)
        
        if results == "CONNECTION_ERROR":
            # 如果 Everything 不可用，使用 Python 的 os.listdir 作为备用
            import os
            if not parent_path or not os.path.exists(parent_path):
                return {"results": []}
            
            results = []
            try:
                for item in os.listdir(parent_path):
                    item_path = os.path.join(parent_path, item)
                    if os.path.exists(item_path):
                        stat = os.stat(item_path)
                        is_dir = os.path.isdir(item_path)
                        
                        file_info = {
                            "name": item,
                            "path": item_path,
                            "size": "0 B" if is_dir else format_size(stat.st_size),
                            "size_bytes": 0 if is_dir else stat.st_size,
                            "modified": format_time(stat.st_mtime),
                            "type": "folder" if is_dir else "file"
                        }
                        results.append(file_info)
            except PermissionError:
                # 如果没有权限访问，返回空列表
                results = []
                
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取文件列表失败: {str(e)}"
        )

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def format_time(timestamp):
    """格式化时间戳"""
    import datetime
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "-"

@router.get("/api/vector_search")
def vector_search(q: str, k: int = 30):
    """
    向量檢索接口
    :param q: 搜索關鍵詞
    :param k: 返回結果數量
    """
    if not q:
        return {"results": []}

    try:
        # 獲取系統實例 (懶加載)
        embedder = system.get_embedding_model()
        store = system.get_vector_store()
        
        if not store or not hasattr(store, 'index') or store.index is None or store.index.ntotal == 0:
            return {"results": [], "msg": "向量數據庫為空或未初始化"}

        # 1. 生成查詢向量
        start_time = time.time()
        query_vector = embedder.encode(q)[0]
        
        # 2. 執行檢索
        results = store.search(query_vector, k=k)
        end_time = time.time()
        
        # 3. 控制台輸出結果 (僅顯示前10個)
        console_display_count = min(10, len(results))
        print("\n" + "="*50)
        print(f"向量搜索結果 (關鍵詞: '{q}') - 返回前 {len(results)} 個結果，控制台顯示前 {console_display_count} 個")
        print("="*50)
        print("Score說明: L2距離，數值越小越相似 (0為完全相同)")
        print("UI轉換: 相似度 = 1/(1+score)，範圍0-1，越接近1越相似")
        print("-"*50)
        for i, res in enumerate(results[:console_display_count]):  # 只顯示前10個
            score = res.get('score', 0)
            similarity = 1 / (1 + score)  # UI顯示的相似度
            file_path = res.get('file_path', 'Unknown')
            # 兼容前端：同时支持 chunk_text 和 content 字段
            content = res.get('chunk_text', res.get('content', ''))[:100] + "..."
            print(f"[{i+1}] L2距離: {score:.4f} | 相似度: {similarity:.4f} | File: {file_path}")
            print(f"    Content: {content}")
            print("-" * 30)
        print(f"搜索耗時: {end_time - start_time:.4f}s")
        print("="*50 + "\n")
        
        # 确保返回结果包含 content 字段以兼容前端
        for res in results:
            if 'chunk_text' in res and 'content' not in res:
                res['content'] = res['chunk_text']
        
        return {"results": results}
        
    except Exception as e:
        print(f"向量搜索出錯: {e}")
        raise HTTPException(status_code=500, detail=str(e))
