import math
from typing import List, Dict, Any

from backend.RAG.SystemManager import system
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
    import datetime
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "-"


def merge_chunks_by_file(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    按文件合併分块結果，每個文件只保留最佳分块
    """
    file_dict: Dict[str, Dict[str, Any]] = {}

    for chunk in chunks:
        file_path = chunk.get('file_path', '')
        score = chunk.get('score', float('inf'))

        if file_path not in file_dict:
            file_dict[file_path] = {
                'best_chunk': chunk.copy(),
                'all_chunks': [chunk.copy()]
            }
            file_dict[file_path]['best_chunk']['chunk_count'] = 1
        elif score < file_dict[file_path]['best_chunk']['score']:
            file_dict[file_path]['best_chunk'] = chunk.copy()
            file_dict[file_path]['best_chunk']['chunk_count'] = len(file_dict[file_path]['all_chunks']) + 1
            file_dict[file_path]['all_chunks'].append(chunk.copy())
        else:
            file_dict[file_path]['all_chunks'].append(chunk.copy())
            file_dict[file_path]['best_chunk']['chunk_count'] += 1

    merged_results = []
    for file_path, data in file_dict.items():
        best_chunk = data['best_chunk']
        best_chunk['all_chunks'] = data['all_chunks']
        merged_results.append(best_chunk)

    merged_results.sort(key=lambda x: x['score'])

    return merged_results


def apply_filters(
    file_results: List[Dict[str, Any]],
    extensions: set = None,
    min_size: int = None,
    max_size: int = None,
    min_modified: str = None,
    max_modified: str = None
) -> List[Dict[str, Any]]:
    """
    应用过滤条件到文件结果
    """
    filtered_results = []

    for file in file_results:
        file_path = file.get('file_path', '')
        size_bytes = file.get('size_bytes', 0)
        modified_timestamp = file.get('modified_timestamp', 0)

        if extensions:
            file_ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
            if file_ext not in extensions:
                continue

        if min_size is not None and size_bytes < min_size:
            continue
        if max_size is not None and size_bytes > max_size:
            continue

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
    """
    if total_chunks <= 0:
        return 0

    log_base = 1.25 + (k - 1) * 0.30 / 9

    if total_chunks >= 1:
        extract_count = 7 * math.log(total_chunks, log_base)
    else:
        extract_count = 50

    extract_count = int(round(extract_count))
    extract_count = max(50, min(total_chunks, extract_count))

    return extract_count


QUERY_REWRITE_TEMPLATE = """这是一个语义文件检索系统。你的任务是将用户查询改写为更有利于向量检索的搜索表达。

优化目标：
1. 保留原始核心语义
2. 扩展相关关键词（同义词、相关术语、常见表达）
3. 使用“关键词组合”而不是长句解释
4. 尽量覆盖用户可能想查找的不同表达方式
5. 避免无关扩展和过度解释

改写要求：
* 输出应为一个“短语或关键词集合”，可以包含多个表达
* 不要写成完整解释性句子
* 不要添加额外说明或前后缀
* 不要输出多余文本

示例：
用户查询：苹果
改写输出：苹果 水果 苹果营养 苹果特点 水果营养价值

用户查询：缓存怎么优化
改写输出：缓存优化 缓存性能提升 缓存策略 缓存机制 缓存设计

---

这是用户的查询：
{query}
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
        llm = system.load_local_llm(model_name=llm_model)

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
