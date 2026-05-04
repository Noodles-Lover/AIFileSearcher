import os
from typing import Dict, Any
from .SemiStructuredProcessor import SemiStructuredProcessor


class ParquetParser(SemiStructuredProcessor):
    """
    Parquet / Feather 列式存储文件解析器 (.parquet, .feather)
    提取表结构和数据样本，使用 LLM 生成描述
    """

    type = "parquet"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._columns: list = []
        self._row_count: int = 0
        self._dtypes: Dict[str, str] = {}

    def _extract_content(self) -> str:
        try:
            import pandas as pd
        except ImportError:
            print(f"❌ pandas 不可用，无法解析 {self.file_path}")
            return ""

        try:
            ext = os.path.splitext(self.file_path)[1].lower()

            if ext == ".parquet":
                df = pd.read_parquet(self.file_path)
            elif ext == ".feather":
                df = pd.read_feather(self.file_path)
            else:
                df = pd.read_parquet(self.file_path)

            self._columns = list(df.columns)
            self._row_count = len(df)
            self._dtypes = {col: str(df[col].dtype) for col in df.columns}

            text = []

            # 表结构
            text.append("=== 列信息 ===")
            for col in self._columns:
                text.append(f"  {col}: {self._dtypes[col]}")

            text.append(f"\n行数: {self._row_count}")

            # 数据样本（前5行）
            if self._row_count > 0:
                text.append("\n=== 数据样本（前5行）===")
                text.append("\t".join(self._columns))
                for _, row in df.head(5).iterrows():
                    row_text = [str(v) if pd.notna(v) else "" for v in row]
                    text.append("\t".join(row_text))

            # 数值列统计摘要
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            if numeric_cols:
                text.append("\n=== 数值统计 ===")
                for col in numeric_cols[:10]:
                    stats = df[col].describe()
                    text.append(f"  {col}: 均值={stats.get('mean', 'N/A'):.2f}, "
                                f"最小={stats.get('min', 'N/A')}, 最大={stats.get('max', 'N/A')}")

            extracted = "\n".join(text)
            return extracted if extracted.strip() else ""

        except Exception as e:
            print(f"❌ 读取 Parquet/Feather 文件失败 {self.file_path}: {e}")
            return ""

    def _get_description_prompt(self, content_preview: str) -> str:
        file_name = os.path.basename(self.file_path)
        ext = os.path.splitext(self.file_path)[1].lower()

        return f"""请用自然语言描述以下{ext.upper()}数据文件，描述将用于语义检索，请包含用户可能搜索的关键信息。

要求：
- 说明这是什么数据、关于什么内容（如：城市经济数据、机器学习训练数据等）
- 包含数据中的字段/列名（用户可能搜索"包含xxx字段的数据"）
- 包含数据中出现的具体名称、项目名、类别等（用户可能直接搜索这些名称）
- 提及数据涉及的时间范围、地域范围等（如果有）
- 用你向别人介绍这个数据文件内容时会用的自然语言来写

文件名：{file_name}

数据内容：
{content_preview}"""

    def _get_fallback_description(self) -> str:
        file_name = os.path.basename(self.file_path)
        ext = os.path.splitext(self.file_path)[1].lower()
        parts = [f"{ext.upper()}数据文件 {file_name}"]
        if self._columns:
            parts.append(f"列: {', '.join(self._columns[:10])}")
        if self._content:
            preview = self._content[:300].replace("\n", " ")
            parts.append(preview)
        return " ".join(parts)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **super().metadata,
            "columns": self._columns,
            "row_count": self._row_count,
            "dtypes": self._dtypes,
            "parser": "ParquetParser",
        }
