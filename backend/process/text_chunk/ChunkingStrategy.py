from abc import ABC, abstractmethod
from typing import List, Dict


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


class FixedSizeChunking(ChunkingStrategy):
    """
    固定字符数分块策略
    """
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += max(1, self.chunk_size - self.overlap)
        return chunks

    def __str__(self):
        return f"FixedSizeChunking(size={self.chunk_size}, overlap={self.overlap})"


class SentenceChunking(ChunkingStrategy):
    """
    基于句子的分块策略 (简单示例，实际可依赖 nltk/spacy)
    """
    def __init__(self, max_tokens: int = 200):
        self.max_tokens = max_tokens

    def chunk(self, text: str) -> List[str]:
        sentences = text.replace('。', '.').split('.')
        chunks = []
        current_chunk = ""

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(current_chunk) + len(sent) > self.max_tokens:
                chunks.append(current_chunk)
                current_chunk = sent
            else:
                current_chunk += ". " + sent if current_chunk else sent

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def __str__(self):
        return f"SentenceChunking(max_tokens={self.max_tokens})"


class ParagraphChunking(ChunkingStrategy):
    """
    基于段落的分块策略
    """
    def chunk(self, text: str) -> List[str]:
        return [p.strip() for p in text.split('\n\n') if p.strip()]

    def __str__(self):
        return "ParagraphChunking"


ChunkingStrategy.DEFAULT_STRATEGIES = {
    '.md': ParagraphChunking(),
    '.txt': FixedSizeChunking(chunk_size=1000, overlap=100),
    '.pdf': FixedSizeChunking(chunk_size=500, overlap=50),
    '.docx': FixedSizeChunking(chunk_size=500, overlap=50),
    '.doc': FixedSizeChunking(chunk_size=500, overlap=50),
    '.pptx': FixedSizeChunking(chunk_size=500, overlap=50),
    '.ppt': FixedSizeChunking(chunk_size=500, overlap=50),
}
