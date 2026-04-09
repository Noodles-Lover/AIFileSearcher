import sys
import os
import time
import json
from typing import List, Dict, Any

from backend.utils.path_utils import ensure_project_path

ensure_project_path()

from fastapi import APIRouter, HTTPException
from .everything import EverythingClient
from backend.RAG.SystemManager import system
from backend.utils.settings_manager import settings_manager

router = APIRouter()

client = EverythingClient()

@router.get("/api/list")
def list_files(parent_path: str = "", recursive: bool | None = None):
    """
    列出指定目錄下的文件（递归遍历子文件夹）
    """
    try:
        # 首先尝试使用 Everything (递归遍历)
        if recursive is None:
            recursive = bool(settings_manager.load().get("include_subfolders", False))

        results = client.get_files_in_folder(parent_path, recursive=recursive)
        
        if results == "CONNECTION_ERROR":
            # 如果 Everything 不可用，使用 Python 的 os.walk 作为备用（递归遍历）
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
                    if not recursive:
                        break
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
def vector_search(q: str, k: int = 30, decay_rate: int = 5, 
                  file_extensions: str = None, min_size: int = None, 
                  max_size: int = None, min_modified: str = None, 
                  max_modified: str = None):
    """
    向量檢索接口
    :param q: 搜索關鍵詞
    :param k: 返回結果數量 (按文件計算)
    :param decay_rate: 衰減率 (1-10)，-1表示使用設置中的值
    :param file_extensions: 文件擴展名過濾，逗號分隔，如 "pdf,docx,txt"
    :param min_size: 最小文件大小（字節）
    :param max_size: 最大文件大小（字節）
    :param min_modified: 最小修改時間（時間戳）
    :param max_modified: 最大修改時間（時間戳）
    """
    if not q:
        return {"results": []}

    try:
        # 獲取系統實例 (懶加載)
        embedder = system.get_embedding_model()
        store = system.get_vector_store()
        
        if not store or not hasattr(store, 'index') or store.index is None or store.index.ntotal == 0:
            return {"results": [], "msg": "向量數據庫為空或未初始化"}

        # 獲取文件緩存
        from backend.RAG.FileCache import FileCache
        from backend.utils.path_utils import get_data_path
        cache_path = get_data_path("file_cache.json")
        file_cache = FileCache(cache_path)

        # 解析過濾條件
        extensions = set(ext.lower() for ext in file_extensions.split(',')) if file_extensions else None

        # 1. 生成查詢向量
        start_time = time.time()
        query_vector = embedder.encode(q)[0]
        
        # 2. 執行檢索 (使用动态算法计算需要提取的分块数量)
        total_chunks = store.index.ntotal
        chunk_count = calculate_dynamic_chunk_count(decay_rate if decay_rate > 0 else 5, total_chunks)
        print(f"[搜索参数] 衰减率k: {decay_rate if decay_rate > 0 else 5}, 总分块数: {total_chunks}, 计算分块数: {chunk_count}")
        chunk_results = store.search(query_vector, k=chunk_count)
        end_time = time.time()
        
        # 3. 按文件合併結果
        file_results = merge_chunks_by_file(chunk_results)
        
        # 4. 從文件緩存獲取文件信息並添加到結果中
        for res in file_results:
            file_path = res.get('file_path', '')
            metadata = file_cache.get_file_metadata(file_path)
            if metadata:
                res['size'] = format_size(metadata.get('fileSize', 0))
                res['size_bytes'] = metadata.get('fileSize', 0)
                res['modified'] = format_time(metadata.get('modified_time', 0))
                res['modified_timestamp'] = metadata.get('modified_time', 0)
            else:
                res['size'] = '-'
                res['size_bytes'] = 0
                res['modified'] = '-'
                res['modified_timestamp'] = 0
        
        # 5. 應用過濾條件
        original_chunk_count = len(chunk_results)
        file_results = apply_filters(file_results, extensions, min_size, max_size, min_modified, max_modified)
        filtered_chunk_count = sum(file.get('chunk_count', 1) for file in file_results)
        
        # 6. 動態調整k值（如果過濾後減少超過35%）
        # 当decay_rate为-1时，使用设置中的默认值5
        current_decay_rate = decay_rate if decay_rate > 0 else 5
        if current_decay_rate > 0 and original_chunk_count > 0:
            reduction_ratio = (original_chunk_count - filtered_chunk_count) / original_chunk_count
            if reduction_ratio > 0.35: 
                # 過濾減少超過35%，需要重新搜索
                reduction_percent = reduction_ratio * 100
                print(f"\n[過濾提示] 從 {original_chunk_count} 個分塊減少到了 {filtered_chunk_count} 個分塊 ({reduction_percent:.1f}%)，將進行再次檢索")
                
                for attempt in range(2):  # 最多重試2次
                    new_decay_rate = current_decay_rate - 1
                    if new_decay_rate < 1:
                        break
                    
                    chunk_count = calculate_dynamic_chunk_count(new_decay_rate, total_chunks)
                    print(f"[搜索参数] 衰减率k: {new_decay_rate}, 总分块数: {total_chunks}, 计算分块数: {chunk_count}")
                    chunk_results = store.search(query_vector, k=chunk_count)
                    file_results = merge_chunks_by_file(chunk_results)
                    
                    # 添加文件信息
                    for res in file_results:
                        file_path = res.get('file_path', '')
                        metadata = file_cache.get_file_metadata(file_path)
                        if metadata:
                            res['size'] = format_size(metadata.get('fileSize', 0))
                            res['size_bytes'] = metadata.get('fileSize', 0)
                            res['modified'] = format_time(metadata.get('modified_time', 0))
                            res['modified_timestamp'] = metadata.get('modified_time', 0)
                        else:
                            res['size'] = '-'
                            res['size_bytes'] = 0
                            res['modified'] = '-'
                            res['modified_timestamp'] = 0
                    
                    # 應用過濾
                    new_original_chunk_count = len(chunk_results)
                    file_results = apply_filters(file_results, extensions, min_size, max_size, min_modified, max_modified)
                    new_filtered_chunk_count = sum(file.get('chunk_count', 1) for file in file_results)
                    
                    new_reduction_ratio = (new_original_chunk_count - new_filtered_chunk_count) / new_original_chunk_count
                    if new_reduction_ratio > 0.35:
                        new_reduction_percent = new_reduction_ratio * 100
                        print(f"[過濾提示] 從 {new_original_chunk_count} 個分塊減少到了 {new_filtered_chunk_count} 個分塊 ({new_reduction_percent:.1f}%)，將進行再次檢索")
                    
                    if new_reduction_ratio <= 0.35:
                        break
                    
                    current_decay_rate = new_decay_rate
        
        # 7. 選取前 k 個文件
        final_results = file_results[:k]
        
        # 8. 控制台輸出結果 (僅顯示前10個文件)
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
        
        # 2. 搜索所有分块 (获取更多结果以确保包含该文件的所有匹配分块)
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
    """
    file_dict = {}  # {file_path: {best_chunk, all_chunks}}
    
    for chunk in chunks:
        file_path = chunk.get('file_path', '')
        score = chunk.get('score', float('inf'))
        
        # 如果是第一次見到這個文件，或者當前分块的分數更好，則保存
        if file_path not in file_dict:
            # 初始化文件記錄
            file_dict[file_path] = {
                'best_chunk': chunk.copy(),
                'all_chunks': [chunk.copy()]
            }
            file_dict[file_path]['best_chunk']['chunk_count'] = 1
        elif score < file_dict[file_path]['best_chunk']['score']:
            # 更新最佳分块
            file_dict[file_path]['best_chunk'] = chunk.copy()
            file_dict[file_path]['best_chunk']['chunk_count'] = len(file_dict[file_path]['all_chunks']) + 1
            file_dict[file_path]['all_chunks'].append(chunk.copy())
        else:
            # 添加到分块列表
            file_dict[file_path]['all_chunks'].append(chunk.copy())
            file_dict[file_path]['best_chunk']['chunk_count'] += 1
    
    # 转换为列表并按分数排序
    merged_results = []
    for file_path, data in file_dict.items():
        # 将所有分块添加到结果中
        best_chunk = data['best_chunk']
        best_chunk['all_chunks'] = data['all_chunks']
        merged_results.append(best_chunk)
    
    merged_results.sort(key=lambda x: x['score'])
    
    return merged_results

def apply_filters(file_results: List[Dict[str, Any]], 
                  extensions: set = None, 
                  min_size: int = None, 
                  max_size: int = None, 
                  min_modified: str = None, 
                  max_modified: str = None) -> List[Dict[str, Any]]:
    """
    应用过滤条件到文件结果
    :param file_results: 文件结果列表
    :param extensions: 允许的文件扩展名集合（不包含点）
    :param min_size: 最小文件大小（字節）
    :param max_size: 最大文件大小（字節）
    :param min_modified: 最小修改時間（時間戳字符串）
    :param max_modified: 最大修改時間（時間戳字符串）
    :return: 过滤后的文件结果列表
    """
    filtered_results = []
    
    for file in file_results:
        file_path = file.get('file_path', '')
        size_bytes = file.get('size_bytes', 0)
        modified_timestamp = file.get('modified_timestamp', 0)
        
        # 检查文件扩展名
        if extensions:
            file_ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
            if file_ext not in extensions:
                continue
        
        # 检查文件大小
        if min_size is not None and size_bytes < min_size:
            continue
        if max_size is not None and size_bytes > max_size:
            continue
        
        # 检查修改时间
        if min_modified is not None:
            try:
                min_time = int(min_modified)
                if modified_timestamp < min_time:
                    continue
            except (ValueError, TypeError):
                pass
        
        if max_modified is not None:
            try:
                max_time = int(max_modified)
                if modified_timestamp > max_time:
                    continue
            except (ValueError, TypeError):
                pass
        
        filtered_results.append(file)
    
    return filtered_results

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
