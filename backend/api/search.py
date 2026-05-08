import sys
import os
import time
import json
from typing import List, Dict, Any

from backend.utils.path_utils import ensure_project_path

ensure_project_path()

from fastapi import APIRouter, HTTPException
from backend.RAG.SystemManager import SystemManager
from backend.utils.settings_manager import settings_manager
from backend.utils.everything_client import EverythingClient
from backend.utils.search_utils import (
    format_size,
    format_time,
    merge_chunks_by_file,
    apply_filters,
    calculate_dynamic_chunk_count,
    rewrite_query_with_llm,
)

router = APIRouter()

client = EverythingClient()


@router.get("/api/list")
def list_files(parent_path: str = "", recursive: bool | None = None):
    """
    列出指定目錄下的文件（递归遍历子文件夹）
    """
    try:
        if recursive is None:
            recursive = bool(settings_manager.load().get("include_subfolders", False))

        results = client.get_files_in_folder(parent_path, recursive=recursive)

        if results == "CONNECTION_ERROR":
            if not parent_path or not os.path.exists(parent_path):
                return {"results": []}

            results = []
            try:
                for root, dirs, files in os.walk(parent_path):
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
                results = []

        return {"results": results}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取文件列表失败: {str(e)}"
        )


@router.get("/api/vector_search")
def vector_search(q: str, k: int = 30, decay_rate: int = 5,
                  file_extensions: str = None, min_size: int = None,
                  max_size: int = None, min_modified: str = None,
                  max_modified: str = None):
    """
    向量檢索接口
    """
    if not q:
        return {"results": []}

    try:
        sm = SystemManager.get_instance()
        embedder = sm.get_embedding_model()
        store = sm.get_vector_store()

        if not store or not hasattr(store, 'index') or store.index is None or store.index.ntotal == 0:
            return {"results": [], "msg": "向量數據庫為空或未初始化"}

        from backend.RAG.FileCache import FileCache
        from backend.utils.path_utils import get_data_path
        cache_path = get_data_path("file_cache.json")
        file_cache = FileCache(cache_path)

        extensions = set(ext.lower() for ext in file_extensions.split(',')) if file_extensions else None

        original_query = q
        llm_filters = None
        applied_filters = None
        settings = settings_manager.load()
        use_query_rewrite = settings.get("query_rewrite_enabled", False)
        llm_auto_filter_enabled = settings.get("llm_auto_filter_enabled", True)

        if use_query_rewrite:
            try:
                rewrite_result = rewrite_query_with_llm(q)
                if rewrite_result and rewrite_result.get('query'):
                    q = rewrite_result['query']
                    llm_filters = {
                        "extensions": rewrite_result.get("extensions", []),
                        "time_range": rewrite_result.get("time_range"),
                        "size_range": rewrite_result.get("size_range")
                    }

                    # 自动套用LLM识别的过滤器（开启自动过滤时，LLM识别结果始终覆盖前端参数）
                    if llm_auto_filter_enabled:
                        applied_filters = {}
                        if llm_filters["extensions"]:
                            extensions_str = ','.join(llm_filters["extensions"])
                            extensions = set(ext.lower() for ext in extensions_str.split(','))
                            applied_filters["extensions"] = llm_filters["extensions"]
                            print(f"  🤖 LLM覆蓋文件擴展名: {extensions_str}")

                        if llm_filters["time_range"]:
                            time_range = llm_filters["time_range"]
                            if time_range.get("min"):
                                min_modified = time_range["min"]
                                applied_filters["min_modified"] = min_modified
                                print(f"  🤖 LLM覆蓋最小修改時間: {min_modified}")
                            if time_range.get("max"):
                                max_modified = time_range["max"]
                                applied_filters["max_modified"] = max_modified
                                print(f"  🤖 LLM覆蓋最大修改時間: {max_modified}")

                        if llm_filters["size_range"]:
                            size_range = llm_filters["size_range"]
                            if size_range.get("min") is not None:
                                min_size = size_range["min"]
                                applied_filters["min_size"] = min_size
                                print(f"  🤖 LLM覆蓋最小文件大小: {min_size} bytes")
                            if size_range.get("max") is not None:
                                max_size = size_range["max"]
                                applied_filters["max_size"] = max_size
                                print(f"  🤖 LLM覆蓋最大文件大小: {max_size} bytes")

                        if applied_filters:
                            print(f"🤖 LLM自動套用過濾條件: {applied_filters}")
                        else:
                            print(f"🤖 LLM未識別到有效過濾條件")
                else:
                    print(f"\n⚠️ LLM返回了空結果，使用原始查詢: {original_query}")
                    q = original_query
            except Exception as llm_error:
                print(f"\n❌ LLM查詢重寫失敗: {llm_error}，使用原始查詢: {original_query}")
                q = original_query

        start_time = time.time()
        query_vector = embedder.encode(q)[0]

        total_chunks = store.index.ntotal
        chunk_count = calculate_dynamic_chunk_count(decay_rate if decay_rate > 0 else 5, total_chunks)
        print(f"[搜索参数] 衰减率k: {decay_rate if decay_rate > 0 else 5}, 总分块数: {total_chunks}, 计算分块数: {chunk_count}")
        chunk_results = store.search(query_vector, k=chunk_count)
        end_time = time.time()

        file_results = merge_chunks_by_file(chunk_results)

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

        original_chunk_count = len(chunk_results)
        file_results = apply_filters(file_results, extensions, min_size, max_size, min_modified, max_modified)
        filtered_chunk_count = sum(file.get('chunk_count', 1) for file in file_results)

        current_decay_rate = decay_rate if decay_rate > 0 else 5
        if current_decay_rate > 0 and original_chunk_count > 0:
            reduction_ratio = (original_chunk_count - filtered_chunk_count) / original_chunk_count
            if reduction_ratio > 0.35:
                reduction_percent = reduction_ratio * 100
                print(f"\n[過濾提示] 從 {original_chunk_count} 個分塊減少到了 {filtered_chunk_count} 個分塊 ({reduction_percent:.1f}%)，將進行再次檢索")

                for attempt in range(2):
                    new_decay_rate = current_decay_rate - 1
                    if new_decay_rate < 1:
                        break

                    chunk_count = calculate_dynamic_chunk_count(new_decay_rate, total_chunks)
                    print(f"[搜索参数] 衰减率k: {new_decay_rate}, 总分块数: {total_chunks}, 计算分块数: {chunk_count}")
                    chunk_results = store.search(query_vector, k=chunk_count)
                    file_results = merge_chunks_by_file(chunk_results)

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

        final_results = file_results[:k]

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
            similarity = 1 / (1 + score)
            file_path = res.get('file_path', 'Unknown')
            content = res.get('content', '')[:100] + "..."
            chunk_count = res.get('chunk_count', 1)
            print(f"[{i+1}] L2距離: {score:.4f} | 相似度: {similarity:.4f} | File: {file_path} ({chunk_count}個分块)")
            print(f"    Content: {content}")
            print("-" * 30)
        print(f"搜索耗時: {end_time - start_time:.4f}s")
        print("="*50 + "\n")

        for res in final_results:
            if 'chunk_text' in res and 'content' not in res:
                res['content'] = res['chunk_text']

        response_data = {"results": final_results}

        # 返回LLM识别的过滤条件
        if llm_filters:
            response_data["llm_filters"] = llm_filters
        if applied_filters:
            response_data["applied_filters"] = applied_filters

        return response_data

    except Exception as e:
        print(f"向量搜索出錯: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/file_chunks")
def get_file_chunks(q: str, file_path: str):
    """
    获取指定文件在搜索中的所有匹配分块
    """
    if not q or not file_path:
        return {"chunks": []}

    try:
        sm = SystemManager.get_instance()
        embedder = sm.get_embedding_model()
        store = sm.get_vector_store()

        if not store or not hasattr(store, 'index') or store.index is None or store.index.ntotal == 0:
            return {"chunks": [], "msg": "向量數據庫為空或未初始化"}

        query_vector = embedder.encode(q)[0]

        all_chunks = store.search(query_vector, k=1000)

        file_chunks = []
        for chunk in all_chunks:
            if chunk.get('file_path', '') == file_path:
                chunk_with_content = chunk.copy()
                if 'chunk_text' in chunk_with_content and 'content' not in chunk_with_content:
                    chunk_with_content['content'] = chunk_with_content['chunk_text']
                file_chunks.append(chunk_with_content)

        file_chunks.sort(key=lambda x: x.get('score', float('inf')))

        print(f"文件分块查询: {file_path} - 找到 {len(file_chunks)} 个匹配分块")

        return {"chunks": file_chunks}

    except Exception as e:
        print(f"获取文件分块出錯: {e}")
        raise HTTPException(status_code=500, detail=str(e))
