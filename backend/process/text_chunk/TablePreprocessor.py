"""
表格预处理器
通用表格标准化模块

职责：
1. 标准化表格格式为 Markdown
2. 提供表格识别、提取、移除等工具方法
3. 所有 Parser 统一调用此类处理表格
"""
import re
from typing import List, Tuple


class TablePreprocessor:
    """
    通用表格预处理器

    功能：
    1. preprocess(): 标准化表格格式（保留位置）
    2. extract_tables(): 提取所有表格
    3. remove_tables(): 移除所有表格
    4. is_table_row(): 判断是否为表格行
    """

    @staticmethod
    def is_table_row(line: str) -> bool:
        """
        判断是否为 Markdown 表格行

        Args:
            line: 单行文本

        Returns:
            True 如果是表格行（非分隔行，且至少2列）
        """
        stripped = line.strip()
        if not stripped.startswith('|') or not stripped.endswith('|'):
            return False
        # 排除分隔行（如 |---|---|）
        if re.match(r'^\|[\s\-:|]+\|$', stripped):
            return False
        return stripped.count('|') >= 3  # 至少两列 = 3个|

    @staticmethod
    def preprocess(text: str) -> str:
        """
        对文本进行表格预处理（标准化格式，保留表格位置）

        Args:
            text: 原始文本（可能包含各种格式的表格）

        Returns:
            处理后的文本，表格已标准化为 Markdown 格式
        """
        lines = text.split('\n')
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检测表格开始
            if TablePreprocessor.is_table_row(line):
                table_lines = [line]
                i += 1

                # 收集表格所有行
                while i < len(lines):
                    next_line = lines[i]
                    if TablePreprocessor.is_table_row(next_line):
                        table_lines.append(next_line)
                        i += 1
                    elif TablePreprocessor._is_separator_row(next_line):
                        # 跳过分隔行
                        i += 1
                    else:
                        break

                # 格式化表格
                formatted_table = TablePreprocessor.format_table(table_lines)
                result_lines.append(formatted_table)
            else:
                result_lines.append(line)
                i += 1

        return '\n'.join(result_lines)

    @staticmethod
    def extract_tables(text: str) -> List[str]:
        """
        从文本中提取所有表格

        Args:
            text: 原始文本

        Returns:
            表格列表（已格式化为标准 Markdown）
        """
        tables = []
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            if TablePreprocessor.is_table_row(line):
                table_lines = [line]
                i += 1

                while i < len(lines):
                    if TablePreprocessor.is_table_row(lines[i]):
                        table_lines.append(lines[i])
                        i += 1
                    elif TablePreprocessor._is_separator_row(lines[i]):
                        i += 1
                    else:
                        break

                if table_lines:
                    tables.append(TablePreprocessor.format_table(table_lines))
            else:
                i += 1

        return tables

    @staticmethod
    def remove_tables(text: str) -> str:
        """
        从文本中移除所有表格

        Args:
            text: 原始文本

        Returns:
            移除了表格的文本
        """
        lines = text.split('\n')
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if TablePreprocessor.is_table_row(line):
                # 跳过整个表格
                while i < len(lines):
                    if TablePreprocessor.is_table_row(lines[i]):
                        i += 1
                    elif TablePreprocessor._is_separator_row(lines[i]):
                        i += 1
                    else:
                        break
            else:
                result_lines.append(line)
                i += 1

        return '\n'.join(result_lines)

    @staticmethod
    def _is_separator_row(line: str) -> bool:
        """判断是否为表格分隔行"""
        stripped = line.strip()
        return bool(re.match(r'^\|[\s\-:|]+\|$', stripped))

    @staticmethod
    def format_table(table_lines: List[str]) -> str:
        """
        将表格行格式化为标准 Markdown 格式

        Args:
            table_lines: 表格的所有行（原始格式）

        Returns:
            标准化的 Markdown 表格字符串
        """
        if not table_lines:
            return ""

        # 解析表格结构
        rows = []
        for line in table_lines:
            # 去掉首尾的 |，分割单元格
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            rows.append(cells)

        if not rows:
            return ""

        # 确认所有行有相同的列数
        col_count = max(len(row) for row in rows)
        normalized_rows = []
        for row in rows:
            # 补齐或截断列
            if len(row) < col_count:
                row.extend([''] * (col_count - len(row)))
            normalized_rows.append(row[:col_count])

        # 格式化输出
        formatted_lines = []

        # 表头
        formatted_lines.append('| ' + ' | '.join(normalized_rows[0]) + ' |')

        # 分隔行
        formatted_lines.append('| ' + ' | '.join(['---'] * col_count) + ' |')

        # 数据行
        for row in normalized_rows[1:]:
            formatted_lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(formatted_lines)
