import math
from typing import List, Dict, Any

from backend.RAG.SystemManager import SystemManager
from backend.utils.settings_manager import settings_manager
from datetime import datetime, timedelta


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
        # modified_timestamp=0 表示时间未知，不应用时间过滤
        if min_modified and modified_ts > 0:
            from datetime import datetime
            try:
                min_ts = datetime.strptime(min_modified, "%Y-%m-%d").timestamp()
                if modified_ts < min_ts:
                    continue
            except ValueError:
                pass

        if max_modified and modified_ts > 0:
            from datetime import datetime
            try:
                max_ts = datetime.strptime(max_modified, "%Y-%m-%d").timestamp()
                if modified_ts > max_ts:
                    continue
            except ValueError:
                pass

        filtered.append(file_info)

    return filtered


def calculate_dynamic_chunk_count(k: int, total_chunks: int) -> int:
    """
    动态计算需要提取的分块数量
    使用简单对数函数 y = 7 * log_k(x)

    Args:
        k: 用户设置的衰减率 (1-10)，会映射到 log_base 1.25-1.55
        total_chunks: 总chunk数量

    Returns:
        实际搜索的chunk数量 (范围: 50 到 total_chunks)
    """
    import math

    if total_chunks <= 0:
        return 90  # 默认值

    # 将用户衰减率1-10映射到log_base=1.25-1.55
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


QUERY_REWRITE_TEMPLATE = """这是一个语义文件检索系统。你的任务是分析用户查询，提取搜索关键词和过滤条件。

当前日期：{current_date}

你的任务是：
1. 将用户查询改写为更有利于向量检索的关键词（保留核心语义，扩展同义词）
2. 识别用户可能想要过滤的条件：
   - 文件扩展名（extensions）：用户提到的文件类型，如 .pdf, .docx
   - 修改时间范围（time_range）：用户提到的时间范围，如"最近一周"、"上个月"、"2024年"
   - 文件大小范围（size_range）：用户提到的文件大小，如"大于1MB"、"小于100KB"

输出格式要求：
必须输出严格的JSON格式，包含以下字段：
{{
  "query": "改写后的搜索关键词",
  "extensions": [] or [".pdf", ".docx"],  // 如果没有提到文件类型，返回空数组
  "time_range": null or {{"min": "YYYY-MM-DD", "max": "YYYY-MM-DD"}},  // 如果没有提到时间，返回null
  "size_range": null or {{"min": 字节数, "max": 字节数}}  // 如果没有提到大小，返回null
}}

重要提示：
- 时间范围判断要宽泛，避免遗漏目标文件
- 模糊时间计算规则（基于当前日期 {current_date}）：
  * "最近"或"近期"：往前推6个月
  * "今年"：从当年1月1日开始
- 文件大小换算：1KB=1024字节，1MB=1048576字节，1GB=1073741824字节
- 查询词改写规则：保留核心语义，扩展同义词和相关术语，避免使用过于宽泛的词汇（如"算法""模型"），应改写为更具体的术语
- 不要添加任何JSON以外的文本、说明或标记

示例1（含时间范围）：
用户查询：最近修改的PDF文件关于神经网络训练
输出：
{{
  "query": "神经网络 训练方法 反向传播 梯度下降 深度学习",
  "extensions": [".pdf"],
  "time_range": {{"min": "{date_6months_ago}", "max": "{current_date}"}},
  "size_range": null
}}

示例2（含文件大小）：
用户查询：找关于项目进度汇报的PPT，大小超过2MB
输出：
{{
  "query": "项目进度 汇报 里程碑 完成情况 时间线",
  "extensions": [".pptx", ".ppt"],
  "time_range": null,
  "size_range": {{"min": 2097152, "max": null}}
}}

示例3（纯语义查询）：
用户查询：苹果公司的产品发布会
输出：
{{
  "query": "Apple 苹果公司 产品发布 iPhone Mac 发布会 新品",
  "extensions": [],
  "time_range": null,
  "size_range": null
}}

---

这是用户的查询：
{query}
"""


def parse_rewrite_response(response: str) -> Dict[str, Any]:
    """
    解析LLM返回的重写响应，提取JSON数据

    Args:
        response: LLM返回的字符串

    Returns:
        包含query, extensions, time_range, size_range的字典
    """
    import json
    import re

    default_result = {
        "query": response.strip(),
        "extensions": [],
        "time_range": None,
        "size_range": None
    }

    try:
        # 尝试直接解析JSON
        result = json.loads(response.strip())
        if isinstance(result, dict):
            return {
                "query": result.get("query", response.strip()),
                "extensions": result.get("extensions", []),
                "time_range": result.get("time_range"),
                "size_range": result.get("size_range")
            }
    except json.JSONDecodeError:
        pass

    # 如果直接解析失败，尝试提取JSON块
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            if isinstance(result, dict):
                return {
                    "query": result.get("query", response.strip()),
                    "extensions": result.get("extensions", []),
                    "time_range": result.get("time_range"),
                    "size_range": result.get("size_range")
                }
        except json.JSONDecodeError:
            pass

    # 解析失败，返回原始响应作为query
    print(f"⚠️ LLM响应JSON解析失败，使用原始响应作为查询")
    return default_result


def rewrite_query_with_llm(query: str, use_deepseek: bool = True) -> Dict[str, Any]:
    """
    使用 LLM 重写查询，并返回结构化数据

    Args:
        query: 用户查询
        use_deepseek: 是否使用 DeepSeek API (True=API, False=本地模型)

    Returns:
        包含query, extensions, time_range, size_range的字典
    """

    try:
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        # 计算6个月前的日期（按180天近似）
        date_6months_ago = (now - timedelta(days=180)).strftime("%Y-%m-%d")

        if use_deepseek:
            # 使用 DeepSeek API
            from backend.RAG.DeepSeekLLM import DeepSeekLLM
            llm = DeepSeekLLM()
            prompt = QUERY_REWRITE_TEMPLATE.format(query=query, current_date=current_date, date_6months_ago=date_6months_ago)
            rewritten = llm.generate(
                prompt=prompt,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9,
            )
        else:
            # 使用本地模型
            current_settings = settings_manager.load()
            llm_model = current_settings.get("llm_model", "")

            if not llm_model:
                raise ValueError("未配置本地 LLM 模型，请在设置中选择")

            sm = SystemManager.get_instance()
            sm.load_llm(model_name=llm_model)
            llm = sm.get_llm()

            prompt = QUERY_REWRITE_TEMPLATE.format(query=query, current_date=current_date, min_date_6months_ago=min_date_6months_ago)
            rewritten = llm.generate(
                prompt=prompt,
                system_prompt="",
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
            )

        # 解析LLM返回的JSON响应
        result = parse_rewrite_response(rewritten)

        print(f"\n{'='*50}")
        print(f"🔄 LLM查詢重寫")
        print(f"{'='*50}")
        print(f"📝 原始查詢: {query}")
        print(f"✨ 重寫後查詢: {result['query']}")
        if result['extensions']:
            print(f"📎 識別文件類型: {', '.join(result['extensions'])}")
        if result['time_range']:
            print(f"📅 識別時間範圍: {result['time_range']}")
        if result['size_range']:
            print(f"📊 識別大小範圍: {result['size_range']}")
        print(f"{'='*50}\n")

        return result

    except Exception as e:
        raise RuntimeError(f"LLM 调用失败: {str(e)}")
