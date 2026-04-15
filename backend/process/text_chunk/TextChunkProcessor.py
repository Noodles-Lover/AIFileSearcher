import os
from typing import List, Dict, Any, Optional, Type
from backend.process.BaseFileProcessor import BaseFileProcessor
from .ChunkingStrategy import ChunkingStrategy, SlidingWindowChunking, FixedSizeChunking, ParagraphChunking, SentenceChunking


class TextChunkProcessor(BaseFileProcessor):
    PARSER_MAPPING: Dict[str, Type["TextChunkProcessor"]] = {}

    def __init__(
        self,
        file_path: str,
        vector_store=None,
        embedding_model=None,
        chunking_strategy: Optional[ChunkingStrategy] = None,
        llm_client=None,
    ):
        super().__init__(file_path, vector_store, embedding_model, llm_client)
        self.chunking_strategy = chunking_strategy or self._get_default_strategy()
        self._chunks: List[str] = []
        self._parsed_content: str = ""

    def _get_default_strategy(self) -> ChunkingStrategy:
        ext = os.path.splitext(self.file_path)[1].lower()
        return ChunkingStrategy.DEFAULT_STRATEGIES.get(ext, SlidingWindowChunking(chunk_size=500, overlap=50))

    def get_text(self) -> List[str]:
        self._parsed_content = self._extract_content()
        if not self._parsed_content:
            return []

        if self.chunking_strategy:
            self._chunks = self.chunking_strategy.chunk(self._parsed_content)
        else:
            self._chunks = [self._parsed_content]

        return self._chunks

    def _extract_content(self) -> str:
        return ""

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._metadata,
            "content_length": len(self._parsed_content),
            "chunk_count": len(self._chunks),
        }


from .TXTParser import TXTParser
from .PDFParser import PDFParser
from .DocParser import DocParser  # 同时处理 .doc 和 .docx
from .PPTParser import PPTParser
from .MDParser import MDParser
from .ImageParser import ImageParser

TextChunkProcessor.PARSER_MAPPING.update({
    '.txt': TXTParser,
    '.pdf': PDFParser,
    '.doc': DocParser,
    '.docx': DocParser,  # 与 .doc 共用同一解析器
    '.pptx': PPTParser,
    '.ppt': PPTParser,    # 与 .pptx 共用同一解析器
    '.md': MDParser,
    '.png': ImageParser,
    '.jpg': ImageParser,
    '.jpeg': ImageParser,
    '.bmp': ImageParser,
    '.gif': ImageParser,
    '.webp': ImageParser,
})
