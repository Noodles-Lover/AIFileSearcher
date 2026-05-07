import os
from typing import Any, List, Dict, Optional
from enum import Enum
from .BaseFileProcessor import BaseFileProcessor
from .text_chunk import TextChunkProcessor
from .semi_structured import SemiStructuredProcessor
from .binary import BinaryProcessor


class ProcessingMode(Enum):
    TEXT_CHUNK = "text_chunk"
    SEMI_STRUCTURED = "semi_structured"
    BINARY = "binary"


EXTENSION_PROCESSOR = {
    "text_chunk": {
        ".txt", ".md", ".markdown",
        ".pdf", ".doc", ".docx",
        ".pptx", ".ppt",
        # 字幕（清洗后分块）
        ".srt", ".vtt",
        # 邮件（提取正文后分块）
        ".eml",
    },
    "semi_structured": {
        # 表格数据
        ".xlsx",
        ".csv", ".tsv",
        ".parquet", ".feather",
        # 数据库
        ".db", ".sqlite", ".sqlite3",
        # 记录数据
        ".jsonl",
        # 配置/结构化文件
        ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".cfg",
        # 源代码文件
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp",
        ".go", ".rs", ".rb", ".php", ".swift", ".kt",
        ".html", ".htm", ".css", ".scss",
        ".sql", ".ipynb",
        ".sh", ".bash", ".zsh", ".bat",
        # 日志文件
        ".log",
    },
    "binary": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
        ".exe", ".msi", ".bin", ".apk", ".ipa", ".app",
        ".dll", ".so", ".dylib", ".sys",
        ".iso", ".img", ".dmg", ".vhd", ".vhdx",
        ".ttf", ".otf", ".woff", ".woff2",
        ".class", ".pyc", ".o", ".obj", ".a", ".lib",
        ".pem", ".key", ".crt", ".p12",
        ".dump", ".dmp", ".core",
    }
}


PROCESSOR_CLASSES = {
    "text_chunk": TextChunkProcessor,
    "semi_structured": SemiStructuredProcessor,
    "binary": BinaryProcessor,
}


def _get_processor_type(file_path: str) -> Optional[str]:
    ext = os.path.splitext(file_path)[1].lower()
    for proc_type, extensions in EXTENSION_PROCESSOR.items():
        if ext in extensions:
            return proc_type
    return None


class FileProcessor:
    def __init__(
        self,
        processing_mode: ProcessingMode = ProcessingMode.TEXT_CHUNK,
        vector_store=None,
        embedding_model=None,
        llm_client=None,
        chunking_strategy=None,
    ):
        self.processing_mode = processing_mode
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.llm_client = llm_client
        self.chunking_strategy = chunking_strategy

    def set_processing_mode(self, mode: ProcessingMode):
        self.processing_mode = mode

    def set_vector_store(self, vector_store):
        self.vector_store = vector_store

    def set_embedding_model(self, embedding_model):
        self.embedding_model = embedding_model

    def set_llm_client(self, llm_client):
        self.llm_client = llm_client

    def set_chunking_strategy(self, strategy):
        self.chunking_strategy = strategy

    def is_supported_file(self, file_path: str) -> bool:
        return _get_processor_type(file_path) is not None

    def process_file(
        self,
        file_path: str,
        processing_mode: Optional[ProcessingMode] = None,
    ) -> Dict:
        if not os.path.exists(file_path):
            return {"error": "File not found"}

        ext = os.path.splitext(file_path)[1].lower()
        auto_processor_type = _get_processor_type(file_path)

        if not auto_processor_type:
            return {"error": f"Unsupported file type: {ext}"}

        if processing_mode:
            processor_type = processing_mode.value
        else:
            processor_type = auto_processor_type

        processor_cls = PROCESSOR_CLASSES.get(processor_type)
        if not processor_cls:
            return {"error": f"Unsupported processing mode: {processor_type}"}

        parser_cls = processor_cls.get_parser(file_path)
        if not parser_cls:
            return {"error": f"No parser for file type: {ext}"}

        try:
            parser_kwargs = {
                "file_path": file_path,
                "vector_store": self.vector_store,
                "embedding_model": self.embedding_model,
                "llm_client": self.llm_client,
            }
            # 如果有自定义分块策略且是 TextChunkProcessor，传递它
            if self.chunking_strategy and processor_type == "text_chunk":
                parser_kwargs["chunking_strategy"] = self.chunking_strategy
            
            parser = parser_cls(**parser_kwargs)
            
            # 获取分块策略描述
            if processor_type == "text_chunk":
                # TextChunkProcessor 有 chunking_strategy 属性
                strategy_name = str(parser.chunking_strategy) if hasattr(parser, 'chunking_strategy') else "Unknown"
            elif processor_type == "semi_structured":
                strategy_name = "LLM描述"
            elif processor_type == "binary":
                strategy_name = "二进制分析"
            else:
                strategy_name = processor_type
            
            result = parser.get_text()

            if isinstance(result, list):
                return {
                    "file_path": file_path,
                    "type": ext,
                    "metadata": dict(parser.metadata),
                    "content_length": sum(len(t) for t in result),
                    "chunks": result,
                    "chunk_count": len(result),
                    "processing_mode": processor_type,
                    "strategy": strategy_name,
                    "embedding_mode": "text",
                }
            else:
                return {
                    "file_path": file_path,
                    "type": ext,
                    "metadata": dict(parser.metadata),
                    "content_length": len(result),
                    "chunks": [result],
                    "chunk_count": 1,
                    "processing_mode": processor_type,
                    "strategy": strategy_name,
                    "embedding_mode": "text",
                }
        except Exception as e:
            return {"error": str(e)}

    def process_files(
        self,
        file_paths: List[str],
        processing_mode: Optional[ProcessingMode] = None,
    ) -> List[Dict]:
        results = []
        for file_path in file_paths:
            result = self.process_file(file_path, processing_mode)
            if "error" not in result:
                results.append(result)
        return results
