import os
import sqlite3
from typing import Dict, Any
from .SemiStructuredProcessor import SemiStructuredProcessor


class DatabaseParser(SemiStructuredProcessor):
    """
    数据库文件解析器 (.db, .sqlite, .sqlite3)
    提取表结构和数据样本，使用 LLM 生成描述
    """

    type = "database"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._tables: list = []
        self._table_info: Dict[str, Any] = {}

    def _extract_content(self) -> str:
        try:
            conn = sqlite3.connect(self.file_path)
            cursor = conn.cursor()

            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            self._tables = [row[0] for row in cursor.fetchall()]

            text = []

            for table_name in self._tables:
                text.append(f"=== Table: {table_name} ===")

                # 获取表结构
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns = cursor.fetchall()
                col_names = [col[1] for col in columns]
                col_types = [col[2] for col in columns]
                text.append(f"列: {', '.join(f'{n}({t})' for n, t in zip(col_names, col_types))}")

                # 获取行数
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = cursor.fetchone()[0]
                text.append(f"行数: {row_count}")

                # 获取前5行数据样本
                if row_count > 0:
                    cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 5")
                    rows = cursor.fetchall()
                    text.append("\t".join(col_names))
                    for row in rows:
                        row_text = [str(v) if v is not None else "" for v in row]
                        text.append("\t".join(row_text))

                text.append("")
                self._table_info[table_name] = {
                    "columns": list(zip(col_names, col_types)),
                    "row_count": row_count,
                }

            conn.close()
            extracted = "\n".join(text)
            return extracted if extracted.strip() else ""

        except Exception as e:
            print(f"❌ 读取数据库文件失败 {self.file_path}: {e}")
            return ""

    def _get_description_prompt(self, content_preview: str) -> str:
        file_name = os.path.basename(self.file_path)

        return f"""请用自然语言描述以下SQLite数据库文件，描述将用于语义检索，请包含用户可能搜索的关键信息。

要求：
- 说明这是什么数据库、存储了什么内容（如：课程安排数据库、图书借阅数据库等）
- 包含每个表的名称和用途（用户可能搜索表名）
- 包含表中出现的列名/字段名（用户可能搜索"包含xxx字段的表"）
- 包含数据中出现的具体名称、人名、项目名等（用户可能直接搜索这些名称）
- 用你向别人介绍这个数据库内容时会用的自然语言来写

文件名：{file_name}

数据库内容：
{content_preview}"""

    def _get_fallback_description(self) -> str:
        file_name = os.path.basename(self.file_path)
        parts = [f"SQLite数据库 {file_name}"]
        if self._tables:
            parts.append(f"表: {', '.join(self._tables[:5])}")
        if self._content:
            preview = self._content[:300].replace("\n", " ")
            parts.append(preview)
        return " ".join(parts)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **super().metadata,
            "tables": self._tables,
            "table_info": self._table_info,
            "parser": "DatabaseParser",
        }
