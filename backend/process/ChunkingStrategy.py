from abc import ABC, abstractmethod
from typing import List

class ChunkingStrategy(ABC):
    """
    分塊策略接口 (Strategy Pattern)
    定義將文本分割成塊的算法
    """
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass

    def __str__(self):
        return self.__class__.__name__

class FixedSizeChunking(ChunkingStrategy):
    """
    固定字符數分塊策略
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
    基於句子的分塊策略 (簡單示例，實際可依賴 nltk/spacy)
    """
    def __init__(self, max_tokens: int = 200):
        self.max_tokens = max_tokens

    def chunk(self, text: str) -> List[str]:
        # 簡單按句號分割，實際項目應更健壯
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
    基於段落的分塊策略
    """
    def chunk(self, text: str) -> List[str]:
        return [p.strip() for p in text.split('\n\n') if p.strip()]

    def __str__(self):
        return "ParagraphChunking"
