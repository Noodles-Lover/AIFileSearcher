import math
from typing import List, Dict, Any

from backend.RAG.SystemManager import SystemManager
from backend.utils.settings_manager import settings_manager


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def format_time(timestamp: float) -> str:
    """格式化时间戳"""
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def merge_chunks_by_file(chunk_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将属于同一文件的chunks合并，返回文件级别的结果
    """
    file_map: Dict[str, Dict[str, Any]] = {}

    for chunk in chunk_results:
        file_path = chunk.get('file_path', '')
        if not file_path:
            continue

        if file_path not in file_map:
            file_map[file_path] = {
                'file_path': file_path,
                'chunk_count': 0,
                'chunks': [],
                'score': float('inf'),
            }

        file_info = file_map[file_path]
        file_info['chunk_count'] += 1
        file_info['chunks'].append(chunk)

        chunk_score = chunk.get('score', float('inf'))
        if chunk_score < file_info['score']:
            file_info['score'] = chunk_score

        if 'content' not in file_info and 'chunk_text' in chunk:
            file_info['content'] = chunk.get('chunk_text', '')

    result = list(file_map.values())
    result.sort(key=lambda x: x.get('score', float('inf')))
    return result


def apply_filters(
    file_results: List[Dict[str, Any]],
    extensions: set = None,
    min_size: int = None,
    max_size: int = None,
    min_modified: str = None,
    max_modified: str = None,
) -> List[Dict[str, Any]]:
    """
    对文件结果应用过滤器
    """
    filtered = []

    for file_info in file_results:
        if extensions:
            file_ext = file_info.get('file_path', '').split('.')[-1].lower()
            if f'.{file_ext}' not in extensions:
                continue

        size_bytes = file_info.get('size_bytes', 0)
        if min_size is not None and size_bytes < min_size:
            continue
        if max_size is not None and size_bytes > max_size:
            continue

        modified_ts = file_info.get('modified_timestamp', 0)
        if min_modified:
            from datetime import datetime
            try:
                min_ts = datetime.strptime(min_modified, "%Y-%m-%d").timestamp()
                if modified_ts < min_ts:
                    continue
            except ValueError:
                pass

        if max_modified:
            from datetime import datetime
            try:
                max_ts = datetime.strptime(max_modified, "%Y-%m-%d").timestamp()
                if modified_ts > max_ts:
                    continue
            except ValueError:
                pass

        filtered.append(file_info)

    return filtered


def calculate_dynamic_chunk_count(decay_rate: int, total_chunks: int, base_k: int = 30) -> int:
    """
    根据衰减率计算动态的chunk数量

    Args:
        decay_rate: 衰减率，每增加1，搜索的chunk数量减少
        total_chunks: 总chunk数量
        base_k: 基础搜索数量

    Returns:
        实际搜索的chunk数量
    """
    if total_chunks <= base_k:
        return total_chunks

    k = base_k
    decay_rate = max(1, decay_rate)

    while k < total_chunks:
        k = k * (decay_rate + 1)
        if k >= total_chunks:
            return min(total_chunks, k)

    return min(total_chunks, k)


QUERY_REWRITE_TEMPLATE = """请将以下搜索查询改写成更精确、更明确的表述。

原始查询：{query}

要求：
1. 保留原意
2. 使表述更清晰准确
3. 可以添加必要的上下文信息
4. 返回改写后的查询即可，不要其他内容
"""


def rewrite_query_with_llm(query: str) -> str:
    """
    使用LLM重寫查詢
    """
    current_settings = settings_manager.load()
    llm_model = current_settings.get("llm_model", "")

    if not llm_model:
        raise ValueError("未配置LLM模型，請先在設置中選擇LLM模型")

    try:
        sm = SystemManager.get_instance()
        sm.load_llm(model_name=llm_model)
        llm = sm.get_llm()

        prompt = QUERY_REWRITE_TEMPLATE.format(query=query)

        rewritten = llm.generate(
            prompt=prompt,
            system_prompt="",
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
        )

        return rewritten.strip()

    except Exception as e:
        raise RuntimeError(f"LLM調用失敗: {str(e)}")
