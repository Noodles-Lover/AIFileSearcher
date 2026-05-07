import os
import json
from typing import Dict, Any
from .SemiStructuredProcessor import SemiStructuredProcessor


class JSONLParser(SemiStructuredProcessor):
    """
    JSONL (JSON Lines) 文件解析器 (.jsonl)
    提取每行 JSON 记录，使用 LLM 生成描述
    """

    type = "jsonl"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._record_count: int = 0
        self._keys: list = []

    def _extract_content(self) -> str:
        try:
            text = []
            encodings = ["utf-8", "gbk", "latin-1"]

            for encoding in encodings:
                try:
                    with open(self.file_path, "r", encoding=encoding) as f:
                        for i, line in enumerate(f):
                            line = line.strip()
                            if not line:
                                continue

                            try:
                                obj = json.loads(line)
                                self._record_count += 1

                                # 收集所有键名
                                if isinstance(obj, dict):
                                    for key in obj.keys():
                                        if key not in self._keys:
                                            self._keys.append(key)

                                # 前20条记录详细输出
                                if self._record_count <= 20:
                                    text.append(json.dumps(obj, ensure_ascii=False))
                                # 后续只计数
                                elif self._record_count == 21:
                                    text.append("... (后续记录已省略)")

                            except json.JSONDecodeError:
                                # 非 JSON 行，直接保留
                                self._record_count += 1
                                if self._record_count <= 20:
                                    text.append(line)

                    break  # 成功读取，跳出编码循环

                except UnicodeDecodeError:
                    self._record_count = 0
                    self._keys = []
                    text = []
                    continue

            extracted = "\n".join(text)
            return extracted if extracted.strip() else ""

        except Exception as e:
            print(f"❌ 读取 JSONL 文件失败 {self.file_path}: {e}")
            return ""

    def _get_description_prompt(self, content_preview: str) -> str:
        file_name = os.path.basename(self.file_path)

        return f"""根据以下JSONL数据，生成一段用于语义检索的描述文本。

要求：
- 只输出描述文本本身，不要有任何前缀、解释或格式标记
- 说明这些记录是什么内容（如：员工信息记录、商品数据）
- 包含记录中的关键字段名和具体名称
- 根据数据复杂度灵活调整长度：简单记录简短描述，包含多种字段的复杂数据可详细描述

文件名：{file_name}

数据内容：
{content_preview}"""

    def _get_fallback_description(self) -> str:
        file_name = os.path.basename(self.file_path)
        parts = [f"JSONL数据文件 {file_name}"]
        if self._keys:
            parts.append(f"字段: {', '.join(self._keys[:10])}")
        if self._content:
            preview = self._content[:300].replace("\n", " ")
            parts.append(preview)
        return " ".join(parts)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **super().metadata,
            "record_count": self._record_count,
            "keys": self._keys,
            "parser": "JSONLParser",
        }
