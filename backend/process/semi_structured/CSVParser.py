import os
from typing import Dict, Any
from .SemiStructuredProcessor import SemiStructuredProcessor


class CSVParser(SemiStructuredProcessor):
    """
    CSV/TSV 表格文件解析器 (.csv, .tsv)
    提取表格数据，使用 LLM 生成描述
    与 Excel 本质相同，都是表格数据
    """

    type = "csv"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._columns: list = []
        self._row_count: int = 0
        self._delimiter: str = ","

    def _extract_content(self) -> str:
        try:
            import pandas as pd
        except ImportError:
            print(f"❌ pandas 不可用，尝试手动解析 {self.file_path}")
            return self._extract_manually()

        try:
            ext = os.path.splitext(self.file_path)[1].lower()
            self._delimiter = "\t" if ext == ".tsv" else ","

            # 尝试检测编码
            encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        self.file_path,
                        sep=self._delimiter,
                        encoding=encoding,
                        on_bad_lines="skip",
                    )
                    break
                except (UnicodeDecodeError, Exception):
                    continue

            if df is None:
                return self._extract_manually()

            self._columns = list(df.columns)
            self._row_count = len(df)

            text = []

            # 列名
            text.append(f"=== 列: {', '.join(self._columns)} ===")
            text.append(f"行数: {self._row_count}")
            text.append("")

            # 数据内容
            text.append("\t".join(self._columns))
            for _, row in df.iterrows():
                row_text = [str(v) if pd.notna(v) else "" for v in row]
                if any(v.strip() for v in row_text if v):
                    text.append("\t".join(row_text))

            extracted = "\n".join(text)
            return extracted if extracted.strip() else ""

        except Exception as e:
            print(f"❌ pandas 读取 CSV 失败 {self.file_path}: {e}")
            return self._extract_manually()

    def _extract_manually(self) -> str:
        """pandas 不可用时的降级手动解析"""
        import csv

        ext = os.path.splitext(self.file_path)[1].lower()
        self._delimiter = "\t" if ext == ".tsv" else ","

        encodings = ["utf-8", "gbk", "latin-1"]
        text = []

        for encoding in encodings:
            try:
                with open(self.file_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.reader(f, delimiter=self._delimiter)
                    for i, row in enumerate(reader):
                        if i == 0:
                            self._columns = row
                            text.append(f"=== 列: {', '.join(row)} ===")
                            text.append("")
                        if any(cell.strip() for cell in row):
                            text.append("\t".join(row))
                            self._row_count += 1

                # 行数减去表头
                self._row_count = max(0, self._row_count - 1)
                text.insert(1, f"行数: {self._row_count}")

                extracted = "\n".join(text)
                return extracted if extracted.strip() else ""

            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"❌ 手动解析 CSV 失败 {self.file_path}: {e}")
                return ""

        return ""

    def _get_description_prompt(self, content_preview: str) -> str:
        file_name = os.path.basename(self.file_path)
        ext = os.path.splitext(self.file_path)[1].lower()

        return f"""请用自然语言描述以下{ext.upper()}表格文件，描述将用于语义检索，请包含用户可能搜索的关键信息。

要求：
- 说明这是什么数据表、关于什么内容（如：产品销量表、学生成绩表、员工信息表等）
- 包含表格中的列名/字段名（用户可能搜索"包含xxx字段的表"）
- 包含表格中出现的具体实体名称、项目名称、人名等（用户可能直接搜索这些名称）
- 提及数据涉及的时间范围、地域范围等（如果有）
- 用你向别人介绍这个表格内容时会用的自然语言来写

文件名：{file_name}

表格数据：
{content_preview}"""

    def _get_fallback_description(self) -> str:
        file_name = os.path.basename(self.file_path)
        ext = os.path.splitext(self.file_path)[1].lower()
        parts = [f"{ext.upper()}表格 {file_name}"]
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
            "delimiter": self._delimiter,
            "parser": "CSVParser",
        }
