"""
幻灯片分块策略
按幻灯片边界进行切分，短幻灯片自动合并
"""
from typing import List, Dict, Optional, Tuple
from .ChunkingStrategy import ChunkingStrategy


class SlideChunking(ChunkingStrategy):
    """
    幻灯片分块策略

    适用于 PPT/PPTX 格式
    每个幻灯片作为一个独立的 chunk，短幻灯片自动合并到前一个
    """

    def __init__(
        self,
        max_chunk_size: int = 500,
        min_chunk_size: int = 100,
        include_notes: bool = True,
        include_title: bool = False
    ):
        """
        Args:
            max_chunk_size: 单个幻灯片最大字符数，超出则截断
            min_chunk_size: 最小 chunk 字符数，短于此会合并到前一个
            include_notes: 是否包含幻灯片备注
            include_title: 是否提取并包含幻灯片标题
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.include_notes = include_notes
        self.include_title = include_title

    def chunk(self, text: str) -> List[str]:
        """
        对幻灯片文本进行分块，短幻灯片自动合并

        期望的 text 格式：
        [SLIDE:1:标题1]
        内容1-1
        内容1-2
        [备注:]
        备注内容
        [SLIDE:2:标题2]
        内容2-1
        """
        if not text:
            return []

        # 解析幻灯片结构
        slides = self._parse_slide_structure(text)

        if not slides:
            # 如果解析失败，按最大大小硬切分
            return self._fallback_chunking(text)

        # 构建 chunks 并合并短幻灯片
        chunks = []
        current_chunk_parts = []

        for slide in slides:
            chunk_text = self._build_slide_chunk(slide)
            if not chunk_text.strip():
                continue

            # 如果单个幻灯片超出限制，截断
            if len(chunk_text) > self.max_chunk_size:
                chunk_text = chunk_text[:self.max_chunk_size]

            # 合并短幻灯片
            if current_chunk_parts:
                current_text = '\n'.join(current_chunk_parts)
                current_len = len(current_text)

                # 如果当前 chunk + 新幻灯片不超过最大限制
                if current_len + len(chunk_text) <= self.max_chunk_size:
                    current_chunk_parts.append(chunk_text)
                # 如果当前 chunk 足够大，先保存再开新 chunk
                elif current_len >= self.min_chunk_size:
                    chunks.append(current_text)
                    current_chunk_parts = [chunk_text]
                else:
                    # 当前 chunk 太短，合并到前一个
                    if chunks:
                        chunks[-1] += '\n' + current_text
                        current_chunk_parts = [chunk_text]
                    else:
                        # 第一个 chunk 就太短，直接合并
                        current_chunk_parts.append(chunk_text)
            else:
                current_chunk_parts.append(chunk_text)

        # 处理最后一个 chunk
        if current_chunk_parts:
            current_text = '\n'.join(current_chunk_parts)
            # 如果最后一个 chunk 太短，合并到前一个
            if len(current_text) < self.min_chunk_size and chunks:
                chunks[-1] += '\n' + current_text
            else:
                chunks.append(current_text)

        return [c for c in chunks if c.strip()]

    def _parse_slide_structure(self, text: str) -> List[Dict]:
        """
        解析幻灯片文本结构

        Returns:
            List of {slide_num, title, content, notes, start_pos}
        """
        slides = []

        # # 按 [SLIDE:N] 或 [SLIDE:N:标题] 标记分割
        # import re
        # slide_pattern = re.compile(r'\[SLIDE:(\d+)(?::([^\]]*))?\]')

        matches = list(slide_pattern.finditer(text))

        if not matches:
            return []

        for i, match in enumerate(matches):
            slide_num = int(match.group(1))
            title = match.group(2) if match.group(2) else ""

            # 确定内容范围
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            content_block = text[start_pos:end_pos].strip()

            # 解析内容：分离正文和备注
            content, notes = self._parse_content_and_notes(content_block)

            slides.append({
                'slide_num': slide_num,
                'title': title,
                'content': content,
                'notes': notes,
                'start_pos': match.start()
            })

        return slides

    def _parse_content_and_notes(self, content_block: str) -> Tuple[str, str]:
        """分离正文内容和备注"""
        notes_marker = '[备注:]'
        notes = ""

        if notes_marker in content_block:
            parts = content_block.split(notes_marker)
            content = parts[0].strip()
            notes = parts[1].strip() if len(parts) > 1 else ""
        else:
            content = content_block

        return content, notes

    def _build_slide_chunk(self, slide: Dict) -> str:
        """构建单个幻灯片的 chunk 文本"""
        parts = []

        # 添加标题（可选）
        if self.include_title and slide.get('title'):
            parts.append(slide['title'])

        # 添加正文内容
        if slide.get('content'):
            parts.append(slide['content'])

        # 添加备注
        if self.include_notes and slide.get('notes'):
            parts.append(f"[备注] {slide['notes']}")

        return '\n'.join(parts)

    def _fallback_chunking(self, text: str) -> List[str]:
        """当无法解析幻灯片结构时的降级处理"""
        lines = text.split('\n')
        chunks = []
        current = []

        for line in lines:
            if line.strip():
                current.append(line)
                if len('\n'.join(current)) > self.max_chunk_size:
                    chunk = '\n'.join(current)
                    chunks.append(chunk)
                    current = []

        if current:
            chunks.append('\n'.join(current))

        return chunks

    def chunk_with_metadata(self, text: str) -> List[Dict]:
        """
        带元数据的分块（用于需要更多信息的场景）

        Returns:
            List of {chunk_text, slide_num, title, notes}
        """
        slides = self._parse_slide_structure(text)
        results = []

        for slide in slides:
            chunk_text = self._build_slide_chunk(slide)
            if chunk_text.strip():
                if len(chunk_text) > self.max_chunk_size:
                    chunk_text = chunk_text[:self.max_chunk_size] + "\n...(内容已截断)"

                results.append({
                    'chunk_text': chunk_text,
                    'slide_num': slide['slide_num'],
                    'title': slide.get('title', ''),
                    'notes': slide.get('notes', '')
                })

        return results
