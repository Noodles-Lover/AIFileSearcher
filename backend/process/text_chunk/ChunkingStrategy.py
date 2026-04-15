from abc import ABC, abstractmethod
from typing import List, Dict
import re


class ChunkingStrategy(ABC):
    """
    分块策略接口 (Strategy Pattern)
    定义将文本分割成块的算法
    """
    DEFAULT_STRATEGIES: Dict[str, 'ChunkingStrategy'] = {}

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass

    def __str__(self):
        return self.__class__.__name__


class SlidingWindowChunking(ChunkingStrategy):
    """
    滑动窗口分块策略
    固定字符数切分，边界处向前查找断点（限制30字符内），末尾重叠
    """
    def __init__(self, chunk_size: int = 500, overlap: int = 50, min_chunk_size: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            prev_start = start
            end = min(start + self.chunk_size, len(text))
            
            # 如果不是最后一块，在 end 附近找自然断点（限30字符内）
            if end < len(text):
                break_pos = self._find_break_point(text, start, end)
                if break_pos > start:
                    end = break_pos
            
            chunk = text[start:end].strip()
            
            # 小于最小阈值时合并到上一块
            if len(chunk) < self.min_chunk_size:
                if chunks:
                    chunks[-1] += ' ' + chunk
                else:
                    chunks.append(chunk)
            else:
                chunks.append(chunk)
            
            # 下一个起始位置（考虑重叠）
            start = end - self.overlap if self.overlap > 0 else end
            # 确保 start 只向前推进，防止死循环
            if start <= prev_start:
                start = prev_start + self.chunk_size
            if start >= len(text) or start < 0:
                break
        
        return [c for c in chunks if c]

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """
        从 end-1 向 start 方向查找最佳断点（限30字符内）
        断点优先级：句末标点 > 换行 > 空格/逗号
        """
        search_limit = min(30, end - start)
        search_start = end - search_limit
        
        # 优先找句末标点
        for i in range(end - 1, search_start - 1, -1):
            if text[i] in '。！？.!?':
                return i + 1
        
        # 其次找换行符
        for i in range(end - 1, search_start - 1, -1):
            if text[i] == '\n':
                return i + 1
        
        # 最后找空格或逗号
        for i in range(end - 1, search_start - 1, -1):
            if text[i] in ' ，,':
                return i + 1
        
        return end

    def __str__(self):
        return f"SlidingWindow(size={self.chunk_size}, overlap={self.overlap})"


class FixedSizeChunking(ChunkingStrategy):
    """
    固定字符数分块策略
    按固定大小硬切分，无重叠，无断点查找，最简单高效
    """
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def __str__(self):
        return f"FixedSize(size={self.chunk_size})"


class SentenceChunking(ChunkingStrategy):
    """
    基于句子的分块策略
    按句末标点分割，合并句子到限制长度
    """
    def __init__(self, max_chars: int = 500):
        self.max_chars = max_chars

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        # 按中英文句末标点分割
        pattern = r'(?<=[。！？.!?])\s*'
        sentences = [s.strip() for s in re.split(pattern, text) if s.strip()]
        
        chunks = []
        current = ""
        
        for sent in sentences:
            # 超长无标点句子直接硬截断
            if len(sent) > self.max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                for i in range(0, len(sent), self.max_chars):
                    chunk = sent[i:i + self.max_chars]
                    if i + self.max_chars < len(sent):
                        chunks.append(chunk)
                    else:
                        current = chunk
            elif len(current) + len(sent) <= self.max_chars:
                current = (current + " " + sent).strip() if current else sent
            else:
                if current:
                    chunks.append(current)
                current = sent
        
        if current:
            chunks.append(current)
        
        return [c for c in chunks if c]

    def __str__(self):
        return f"Sentence(max_chars={self.max_chars})"


class ParagraphChunking(ChunkingStrategy):
    """
    基于段落的分块策略
    英文按空行分割，中文按固定行数分组，短段落合并到前一段
    """
    def __init__(self, lines_per_para: int = 5, min_para_chars: int = 50):
        self.lines_per_para = lines_per_para
        self.min_para_chars = min_para_chars

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        
        # 英文段落：按空行分割
        if '\n\n' in text:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if len(paragraphs) > 1:
                return self._merge_short_paragraphs(paragraphs)
        
        # 中文段落：按行分组
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        paragraphs = []
        current_lines = []
        
        for line in lines:
            current_lines.append(line)
            if len(current_lines) >= self.lines_per_para:
                para = ' '.join(current_lines)
                if para:
                    paragraphs.append(para)
                current_lines = []
        
        if current_lines:
            para = ' '.join(current_lines)
            if para:
                paragraphs.append(para)
        
        return self._merge_short_paragraphs(paragraphs) if paragraphs else [text.strip()]

    def _merge_short_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """短段落合并到前一段"""
        if not paragraphs:
            return paragraphs
        
        merged = []
        for para in paragraphs:
            if not para:
                continue
            if merged and len(para) < self.min_para_chars:
                merged[-1] += ' ' + para
            else:
                merged.append(para)
        
        return merged

    def __str__(self):
        return f"Paragraph(lines={self.lines_per_para})"


ChunkingStrategy.DEFAULT_STRATEGIES = {
    '.md': ParagraphChunking(),
    '.txt': SlidingWindowChunking(chunk_size=1000, overlap=100, min_chunk_size=100),
    '.pdf': SlidingWindowChunking(chunk_size=500, overlap=50, min_chunk_size=50),
    '.docx': SlidingWindowChunking(chunk_size=500, overlap=50, min_chunk_size=50),
    '.doc': SlidingWindowChunking(chunk_size=500, overlap=50, min_chunk_size=50),
    '.pptx': SlidingWindowChunking(chunk_size=500, overlap=50, min_chunk_size=50),
    '.ppt': SlidingWindowChunking(chunk_size=500, overlap=50, min_chunk_size=50),
}
