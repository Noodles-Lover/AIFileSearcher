"""
Markdown 语义分块策略
按 Markdown 语法结构（标题、代码块、表格）进行语义切分
"""
import re
from typing import List, Dict
from .ChunkingStrategy import ChunkingStrategy
from .TablePreprocessor import TablePreprocessor


class MDSemanticChunking(ChunkingStrategy):
    """
    Markdown 语义分块策略

    分块规则：
    1. 按 H1/H2/H3 标题层级切分
    2. 代码块不可截断
    3. 表格不可截断（作为独立 section）
    4. 短内容自动合并
    """

    def __init__(
        self,
        max_chunk_size: int = 1200,
        min_chunk_size: int = 100,
        max_header_level: int = 3
    ):
        """
        Args:
            max_chunk_size: 最大 chunk 字符数
            min_chunk_size: 最小 chunk 字符数，短于此会合并到前一块
            max_header_level: 最大标题层级（如 3 表示 H1-H3 都可作为切分点）
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_header_level = max_header_level

    def __str__(self):
        return f"MDSemantic(max_size={self.max_chunk_size}, min_size={self.min_chunk_size}, max_level=H{self.max_header_level})"

    def chunk(self, text: str) -> List[str]:
        """对 Markdown 文本进行语义分块"""
        if not text:
            return []

        # 预处理：标准化表格格式
        text = TablePreprocessor.preprocess(text)

        # 解析 Markdown 结构
        sections = self._parse_markdown_structure(text)

        if not sections:
            return [text] if text.strip() else []

        # 构建 chunks
        chunks = []
        current_chunk = {
            'title': '',
            'content_lines': []
        }

        for section in sections:
            section_text = section['text']
            section_title = section.get('title', '')

            # 检查是否需要切分当前 chunk
            current_size = self._calculate_size(current_chunk, section_title, section_text)

            if current_size + len(section_text) > self.max_chunk_size and current_chunk['content_lines']:
                # 提交当前 chunk
                chunk_text = self._build_chunk_text(current_chunk)
                if chunk_text.strip():
                    chunks.append(chunk_text)

                # 如果单个 section 就超出限制，特殊处理
                if len(section_text) > self.max_chunk_size:
                    # 递归切分这个大 section
                    sub_chunks = self._split_large_section(section)
                    chunks.extend(sub_chunks)
                    current_chunk = {'title': '', 'content_lines': []}
                else:
                    current_chunk = {'title': section_title, 'content_lines': [section_text]}
            else:
                # 追加到当前 chunk
                if not current_chunk['title'] and section_title:
                    current_chunk['title'] = section_title
                if section_text.strip():
                    current_chunk['content_lines'].append(section_text)

        # 处理最后一个 chunk
        if current_chunk['content_lines']:
            chunk_text = self._build_chunk_text(current_chunk)
            if chunk_text.strip():
                chunks.append(chunk_text)

        # 合并过短的 chunks
        chunks = self._merge_short_chunks(chunks)

        return [c for c in chunks if c.strip()]

    def _parse_markdown_structure(self, text: str) -> List[Dict]:
        """
        解析 Markdown 文本结构，返回分段列表

        Returns:
            List of {type, level, title, text}
            - type: 'header', 'code_block', 'table', 'content'
        """
        lines = text.split('\n')
        sections = []
        current_content = []
        in_code_block = False
        code_block_content = []
        code_block_start = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # 代码块处理
            if line.strip().startswith('```'):
                if not in_code_block:
                    # 保存当前内容
                    if current_content:
                        content_text = '\n'.join(current_content).strip()
                        if content_text:
                            sections.extend(self._parse_content_sections(content_text))
                        current_content = []

                    # 开始代码块
                    in_code_block = True
                    code_block_content = [line]
                    code_block_start = i
                else:
                    # 结束代码块
                    code_block_content.append(line)
                    sections.append({
                        'type': 'code_block',
                        'level': 0,
                        'title': '',
                        'text': '\n'.join(code_block_content),
                        'line_start': code_block_start,
                        'line_end': i
                    })
                    in_code_block = False
                    code_block_content = []
                i += 1
                continue

            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue

            # 标题检测
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                # 保存当前内容
                if current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        sections.extend(self._parse_content_sections(content_text))
                    current_content = []

                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                sections.append({
                    'type': 'header',
                    'level': level,
                    'title': title,
                    'text': f"{'#' * level} {title}",
                    'line_start': i,
                    'line_end': i
                })
            else:
                current_content.append(line)

            i += 1

        # 处理剩余内容
        if current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                sections.extend(self._parse_content_sections(content_text))

        return sections

    def _parse_content_sections(self, content: str) -> List[Dict]:
        """
        解析普通内容中的子结构（表格等）
        使用 TablePreprocessor 统一处理表格
        """
        sections = []
        lines = content.split('\n')
        current_paragraph = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检测表格（使用统一的 TablePreprocessor）
            if TablePreprocessor.is_table_row(line):
                table_lines = [line]

                # 收集表格所有行
                i += 1
                while i < len(lines):
                    if TablePreprocessor.is_table_row(lines[i]):
                        table_lines.append(lines[i])
                        i += 1
                    elif TablePreprocessor._is_separator_row(lines[i]):
                        i += 1
                    else:
                        break

                # 保存当前段落
                if current_paragraph:
                    para_text = '\n'.join(current_paragraph).strip()
                    if para_text:
                        sections.append({
                            'type': 'content',
                            'level': 0,
                            'title': '',
                            'text': para_text
                        })
                    current_paragraph = []

                # 表格作为独立 section（使用标准化后的格式）
                formatted_table = TablePreprocessor.format_table(table_lines)
                sections.append({
                    'type': 'table',
                    'level': 0,
                    'title': '',
                    'text': formatted_table
                })
            else:
                current_paragraph.append(line)
                i += 1

        # 保存最后段落
        if current_paragraph:
            para_text = '\n'.join(current_paragraph).strip()
            if para_text:
                sections.append({
                    'type': 'content',
                    'level': 0,
                    'title': '',
                    'text': para_text
                })

        return sections

    def _calculate_size(self, chunk: Dict, new_title: str, new_content: str) -> int:
        """计算加入新内容后的预估大小"""
        size = 0
        if chunk['title']:
            size += len(chunk['title']) + 2
        for line in chunk['content_lines']:
            size += len(line) + 1
        if new_title:
            size += len(new_title) + 2
        size += len(new_content)
        return size

    def _build_chunk_text(self, chunk: Dict) -> str:
        """构建单个 chunk 的文本"""
        parts = []
        if chunk['title']:
            parts.append(chunk['title'])
        if chunk['content_lines']:
            parts.append('\n'.join(chunk['content_lines']))
        return '\n'.join(parts)

    def _split_large_section(self, section: Dict) -> List[str]:
        """递归切分过大的 section"""
        text = section['text']
        title = section.get('title', '')

        if len(text) <= self.max_chunk_size:
            return [text] if text.strip() else []

        # 按段落或换行切分
        lines = text.split('\n')
        chunks = []
        current_lines = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1

            if current_size + line_size > self.max_chunk_size and current_lines:
                chunk = '\n'.join(current_lines)
                if chunk.strip():
                    chunks.append(chunk)
                current_lines = [line]
                current_size = line_size
            else:
                current_lines.append(line)
                current_size += line_size

        if current_lines:
            chunk = '\n'.join(current_lines)
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def _merge_short_chunks(self, chunks: List[str]) -> List[str]:
        """合并过短的 chunks 到前一个"""
        if not chunks:
            return chunks

        merged = []
        for chunk in chunks:
            if not chunk.strip():
                continue

            if len(chunk) < self.min_chunk_size and merged:
                merged[-1] += '\n' + chunk
            else:
                merged.append(chunk)

        return merged
