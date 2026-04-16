"""
幻灯片分块策略
按幻灯片边界进行切分，短幻灯片自动合并
"""
import re
from typing import List, Dict, Tuple
from .ChunkingStrategy import ChunkingStrategy


class SlideChunking(ChunkingStrategy):
    """
    幻灯片分块策略

    适用于 PPT/PPTX 格式
    每个幻灯片作为一个独立的 chunk，短幻灯片自动合并到前一个

    期望的 text 格式（由 PPTParser 输出）：
    [SLIDE:1:标题]
    内容1-1
    内容1-2
    [备注:]
    备注内容

    [SLIDE:2:标题]
    内容2-1
    """

    # 幻灯片标记正则：匹配 [SLIDE:序号:标题]
    SLIDE_PATTERN = re.compile(r'\[SLIDE:(\d+):([^\]]*)\]')
    # 备注标记
    NOTES_MARKER = '[备注:]'

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
            include_title: 是否将幻灯片标题作为 chunk 前缀
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.include_notes = include_notes
        self.include_title = include_title

    def chunk(self, text: str) -> List[str]:
        """对幻灯片文本进行分块，短幻灯片自动合并"""
        if not text:
            return []

        # 解析幻灯片结构
        slides = self._parse_slides(text)

        if not slides:
            # 解析失败，降级为按行硬切分
            return self._fallback_chunking(text)

        # 构建 chunks 并合并短幻灯片
        chunks = []
        current_parts = []

        for slide in slides:
            chunk_text = self._build_chunk_text(slide)
            if not chunk_text.strip():
                continue

            # 单个幻灯片超出限制则截断
            if len(chunk_text) > self.max_chunk_size:
                chunk_text = chunk_text[:self.max_chunk_size]

            current_parts.append(chunk_text)
            current_text = '\n'.join(current_parts)

            # 如果当前累积文本超过最大限制，处理当前并开启新的
            if len(current_text) > self.max_chunk_size:
                # 先移除最后一个，加入已完成的 chunks
                current_parts.pop()
                if current_parts:
                    chunks.append('\n'.join(current_parts))
                    current_parts = [chunk_text]
                else:
                    current_parts = [chunk_text]

        # 处理最后一个 chunk
        if current_parts:
            final_text = '\n'.join(current_parts)
            if len(final_text) < self.min_chunk_size and chunks:
                # 太短，合并到前一个
                chunks[-1] += '\n' + final_text
            else:
                chunks.append(final_text)

        return [c for c in chunks if c.strip()]

    def _parse_slides(self, text: str) -> List[Dict]:
        """
        解析幻灯片文本结构

        Returns:
            List of {slide_num, title, content, notes, raw}
        """
        slides = []
        
        # 按 \n\n 分割幻灯片块
        blocks = text.split('\n\n')
        
        for block in blocks:
            if not block.strip():
                continue

            # 解析幻灯片标记
            slide_match = self.SLIDE_PATTERN.match(block.strip())
            if not slide_match:
                continue

            slide_num = int(slide_match.group(1))
            title = slide_match.group(2).strip()
            
            # 提取标记后的内容
            after_marker = block.strip()[slide_match.end():].strip()
            
            # 分离正文和备注
            content, notes = self._split_content_notes(after_marker)

            slides.append({
                'slide_num': slide_num,
                'title': title,
                'content': content,
                'notes': notes,
                'raw': block
            })

        return slides

    def _split_content_notes(self, text: str) -> Tuple[str, str]:
        """分离正文内容和备注"""
        if self.NOTES_MARKER in text:
            parts = text.split(self.NOTES_MARKER, 1)
            content = parts[0].strip()
            notes = parts[1].strip() if len(parts) > 1 else ""
        else:
            content = text.strip()
            notes = ""

        return content, notes

    def _build_chunk_text(self, slide: Dict) -> str:
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
        """无法解析幻灯片结构时的降级处理：按行硬切分"""
        lines = text.split('\n')
        chunks = []
        current = []

        for line in lines:
            if line.strip():
                current.append(line)
                if len('\n'.join(current)) > self.max_chunk_size:
                    chunks.append('\n'.join(current))
                    current = []

        if current:
            chunks.append('\n'.join(current))

        return chunks

    def chunk_with_metadata(self, text: str) -> List[Dict]:
        """
        带元数据的分块

        Returns:
            List of {chunk_text, slide_num, title, notes}
        """
        slides = self._parse_slides(text)
        results = []

        for slide in slides:
            chunk_text = self._build_chunk_text(slide)
            if not chunk_text.strip():
                continue

            if len(chunk_text) > self.max_chunk_size:
                chunk_text = chunk_text[:self.max_chunk_size] + "\n...(内容已截断)"

            results.append({
                'chunk_text': chunk_text,
                'slide_num': slide['slide_num'],
                'title': slide.get('title', ''),
                'notes': slide.get('notes', '')
            })

        return results
