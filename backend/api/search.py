import sys
import os
import time
import json
from typing import List, Dict, Any

from backend.utils.path_utils import ensure_project_path

# 确保项目根目录在路径中
ensure_project_path()

from fastapi import APIRouter, HTTPException
from .everything import EverythingClient
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
    列出指定目錄下的文件（递归遍历子文件夹）
    """
    try:
        # 首先尝试使用 Everything (递归遍历)
        results = client.get_files_in_folder(parent_path, recursive=True)
        
        if results == "CONNECTION_ERROR":
            # 如果 Everything 不可用，使用 Python 的 os.walk 作为备用（递归遍历）
            import os
            if not parent_path or not os.path.exists(parent_path):
                return {"results": []}
            
            results = []
            try:
                # 使用 os.walk 递归遍历所有子文件夹
                for root, dirs, files in os.walk(parent_path):
                    # 处理当前目录中的文件
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            stat = os.stat(file_path)
                            file_info = {
                                "name": file,
                                "path": file_path,
                                "size": format_size(stat.st_size),
                                "size_bytes": stat.st_size,
                                "modified": format_time(stat.st_mtime),
                                "type": "file"
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
    :param k: 返回結果數量 (按文件計算)
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
        
        # 2. 執行檢索 (使用动态算法计算需要提取的分块数量)
        total_chunks = store.index.ntotal
        chunk_count = calculate_dynamic_chunk_count(k, total_chunks)
        chunk_results = store.search(query_vector, k=chunk_count)
        end_time = time.time()
        
        # 3. 按文件合併結果
        file_results = merge_chunks_by_file(chunk_results)
        
        # 4. 選取前 k 個文件
        final_results = file_results[:k]
        
        # 5. 控制台輸出結果 (僅顯示前10個文件)
        console_display_count = min(10, len(final_results))
        print("\n" + "="*50)
        print(f"向量搜索結果 (關鍵詞: '{q}') - 搜索了 {len(chunk_results)} 個分块，合併為 {len(file_results)} 個文件，返回前 {len(final_results)} 個文件")
        print("="*50)
        print("Score說明: L2距離，數值越小越相似 (0為完全相同)")
        print("UI轉換: 相似度 = 1/(1+score)，範圍0-1，越接近1越相似")
        print("文件排序: 按該文件所有分块中的最佳相似度排序")
        print("-"*50)
        for i, res in enumerate(final_results[:console_display_count]):
            score = res.get('score', 0)
            similarity = 1 / (1 + score)  # UI顯示的相似度
            file_path = res.get('file_path', 'Unknown')
            content = res.get('content', '')[:100] + "..."
            chunk_count = res.get('chunk_count', 1)
            print(f"[{i+1}] L2距離: {score:.4f} | 相似度: {similarity:.4f} | File: {file_path} ({chunk_count}個分块)")
            print(f"    Content: {content}")
            print("-" * 30)
        print(f"搜索耗時: {end_time - start_time:.4f}s")
        print("="*50 + "\n")
        
        # 确保返回结果包含 content 字段以兼容前端
        for res in final_results:
            if 'chunk_text' in res and 'content' not in res:
                res['content'] = res['chunk_text']
        
        return {"results": final_results}
        
    except Exception as e:
        print(f"向量搜索出錯: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/file_chunks")
def get_file_chunks(q: str, file_path: str):
    """
    获取指定文件在搜索中的所有匹配分块
    :param q: 搜索關鍵詞
    :param file_path: 文件路徑
    """
    if not q or not file_path:
        return {"chunks": []}

    try:
        # 獲取系統實例
        embedder = system.get_embedding_model()
        store = system.get_vector_store()
        
        if not store or not hasattr(store, 'index') or store.index is None or store.index.ntotal == 0:
            return {"chunks": [], "msg": "向量數據庫為空或未初始化"}

        # 1. 生成查詢向量
        query_vector = embedder.encode(q)[0]
        
        # 2. 搜索所有分块 (获取更多结果以确保包含该文件的所有分块)
        all_chunks = store.search(query_vector, k=1000)  # 获取1000个分块
        
        # 3. 筛选出指定文件的所有分块
        file_chunks = []
        for chunk in all_chunks:
            if chunk.get('file_path', '') == file_path:
                chunk_with_content = chunk.copy()
                if 'chunk_text' in chunk_with_content and 'content' not in chunk_with_content:
                    chunk_with_content['content'] = chunk_with_content['chunk_text']
                file_chunks.append(chunk_with_content)
        
        # 4. 按相似度排序
        file_chunks.sort(key=lambda x: x.get('score', float('inf')))
        
        print(f"文件分块查询: {file_path} - 找到 {len(file_chunks)} 个匹配分块")
        
        return {"chunks": file_chunks}
        
    except Exception as e:
        print(f"获取文件分块出錯: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def merge_chunks_by_file(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    按文件合併分块結果，每個文件只保留最佳分块
    :param chunks: 分块結果列表
    :return: 按文件合併後的結果列表
    """
    file_dict = {}  # {file_path: best_chunk}
    
    for chunk in chunks:
        file_path = chunk.get('file_path', '')
        score = chunk.get('score', float('inf'))
        
        # 如果是第一次見到這個文件，或者當前分块的分數更好，則保存
        if file_path not in file_dict or score < file_dict[file_path]['score']:
            # 複製分块信息並添加額外統計信息
            merged_chunk = chunk.copy()
            merged_chunk['chunk_count'] = 1  # 初始化分块計數
            file_dict[file_path] = merged_chunk
        else:
            # 更新分块計數
            file_dict[file_path]['chunk_count'] += 1
    
    # 轉換為列表並按分數排序
    merged_results = list(file_dict.values())
    merged_results.sort(key=lambda x: x['score'])
    
    return merged_results

def calculate_dynamic_chunk_count(k: int, total_chunks: int) -> int:
    """
    动态计算需要提取的分块数量
    使用简单对数函数 y = 7 * log_k(x)
    
    Args:
        k: 用户设置的衰减率 (1-10)
        total_chunks: 数据库中的总分块数量
        
    Returns:
        需要提取的分块数量
        
    算法设计:
    - y = 7 * log_k(x)，其中k通过用户衰减率映射
    - 用户衰减率1-10映射到k=1.25-1.55
    - 默认衰减率5对应k=1.4
    - 四舍五入，限制在50到总分块数之间
    """
    import math
    
    if total_chunks <= 0:
        return 0  # 默认值
    
    # 将用户衰减率1-10映射到k=1.25-1.55
    # 线性映射: k = 1.25 + (user_k - 1) * (1.55 - 1.25) / (10 - 1)
    log_base = 1.25 + (k - 1) * 0.30 / 9
    
    # 使用对数函数: y = 7 * log_k(x)
    if total_chunks >= 1:
        extract_count = 7 * math.log(total_chunks, log_base)
    else:
        extract_count = 50
    
    # 四舍五入
    extract_count = int(round(extract_count))
    
    # 限制在50到总分块数之间
    extract_count = max(50, min(total_chunks, extract_count))
    
    return extract_count

