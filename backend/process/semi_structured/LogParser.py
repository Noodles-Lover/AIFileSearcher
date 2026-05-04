import os
import re
from typing import Dict, Any
from .SemiStructuredProcessor import SemiStructuredProcessor


class LogParser(SemiStructuredProcessor):
    """
    日志文件解析器 (.log)
    日志文件通常行数很多、内容重复，使用 LLM 生成摘要描述更合适
    """

    type = "log"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._line_count: int = 0
        self._error_count: int = 0
        self._warning_count: int = 0
        self._time_range: str = ""

    def _extract_content(self) -> str:
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"读取日志文件失败 {self.file_path}: {e}")
            return ""

        self._line_count = len(lines)

        # 统计 ERROR 和 WARNING 行数
        error_pattern = re.compile(r'\b(ERROR|CRITICAL|FATAL|SEVERE)\b', re.IGNORECASE)
        warning_pattern = re.compile(r'\b(WARN|WARNING)\b', re.IGNORECASE)
        self._error_count = sum(1 for line in lines if error_pattern.search(line))
        self._warning_count = sum(1 for line in lines if warning_pattern.search(line))

        # 尝试提取时间范围
        time_pattern = re.compile(r'(\d{4}[-/]\d{2}[-/]\d{2}[\sT]\d{2}:\d{2})')
        timestamps = [m.group(1) for line in lines if (m := time_pattern.search(line))]
        if timestamps:
            self._time_range = f"{timestamps[0]} ~ {timestamps[-1]}"

        # 构建内容摘要：头部 + 尾部 + 错误行样本
        parts = []

        # 头部（前 30 行）
        head_lines = lines[:30]
        parts.append("=== 日志头部 ===")
        parts.extend(line.rstrip() for line in head_lines)

        # 错误行样本（最多 20 行）
        if self._error_count > 0:
            error_lines = [line.rstrip() for line in lines if error_pattern.search(line)][:20]
            parts.append(f"\n=== 错误日志（共 {self._error_count} 条，展示前 {len(error_lines)} 条）===")
            parts.extend(error_lines)

        # 尾部（最后 20 行）
        if len(lines) > 30:
            tail_lines = lines[-20:]
            parts.append("\n=== 日志尾部 ===")
            parts.extend(line.rstrip() for line in tail_lines)

        content = "\n".join(parts)
        if len(content) > 5000:
            content = content[:5000] + "\n... (内容过长已截断)"
        return content

    def _get_description_prompt(self, content_preview: str) -> str:
        file_name = os.path.basename(self.file_path)

        return f"""请用自然语言描述以下日志文件，描述将用于语义检索，请包含用户可能搜索的关键信息。

要求：
- 说明这是什么应用或系统的日志（如：Nginx访问日志、Python应用日志、MySQL慢查询日志等）
- 包含日志中出现的关键信息：应用名称、服务名称、模块名称
- 提及日志中出现的错误类型和错误信息（用户可能搜索"xxx报错"、"xxx错误"）
- 提及日志涉及的时间范围
- 用你向别人描述这个日志文件时会用的自然语言来写

文件名：{file_name}

日志内容摘要：
{content_preview}"""

    def _get_fallback_description(self) -> str:
        file_name = os.path.basename(self.file_path)
        parts = [f"日志文件 {file_name}"]
        if self._time_range:
            parts.append(f"时间范围 {self._time_range}")
        if self._content:
            preview = self._content[:300].replace("\n", " ")
            parts.append(preview)
        return " ".join(parts)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **super().metadata,
            "line_count": self._line_count,
            "error_count": self._error_count,
            "warning_count": self._warning_count,
            "time_range": self._time_range,
            "parser": "LogParser",
        }
