import os
from typing import List, Dict, Type, Optional
from .BaseParser import BaseParser
from .TXTParser import TXTParser
from .PDFParser import PDFParser
from .DocxParser import DocxParser
from .PPTParser import PPTParser
from .MDParser import MDParser
from .ChunkingStrategy import ChunkingStrategy, FixedSizeChunking, ParagraphChunking, SentenceChunking

class FileProcessor:
    """
    文件處理器 (FileProcessor)
    負責調度具體的 Parser 和 ChunkingStrategy
    """
    
    # 註冊支持的解析器
    PARSERS: Dict[str, Type[BaseParser]] = {
        '.txt': TXTParser,
        '.pdf': PDFParser,
        '.docx': DocxParser,
        '.pptx': PPTParser,
        '.md': MDParser,
    }

    def __init__(self, default_chunking_strategy: ChunkingStrategy = None):
        if default_chunking_strategy is None:
            # 默認使用固定大小分塊
            self.default_chunking_strategy = FixedSizeChunking(chunk_size=500, overlap=50)
        else:
            self.default_chunking_strategy = default_chunking_strategy

        # 針對不同文件類型的預設策略
        self.type_strategies = {
            '.md': ParagraphChunking(),
            '.txt': FixedSizeChunking(chunk_size=1000, overlap=100),
            # PDF/Docx/PPTX 結構較複雜，固定大小分塊較爲穩妥
            '.pdf': FixedSizeChunking(chunk_size=500, overlap=50),
            '.docx': FixedSizeChunking(chunk_size=500, overlap=50),
            '.pptx': FixedSizeChunking(chunk_size=500, overlap=50),
        }

    def is_supported_file(self, file_path: str) -> bool:
        """
        检查文件是否支持
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.PARSERS

    def process_file(self, file_path: str, chunking_strategy: Optional[ChunkingStrategy] = None) -> Dict:
        """
        處理單個文件：解析 -> 清洗 -> 分塊
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}

        ext = os.path.splitext(file_path)[1].lower()
        parser_cls = self.PARSERS.get(ext)
        
        if not parser_cls:
            return {"error": f"Unsupported file type: {ext}"}

        # 確定使用哪個分塊策略
        # 優先級: 顯式傳入參數 > 文件類型特定策略 > 默認策略
        if chunking_strategy:
            strategy = chunking_strategy
        else:
            strategy = self.type_strategies.get(ext, self.default_chunking_strategy)

        try:
            # 實例化 Parser 並注入策略
            parser = parser_cls(file_path, strategy)
            
            # 執行模板方法
            chunks = parser.process()
            
            return {
                "file_path": file_path,
                "type": ext,
                "metadata": parser.metadata,
                "content_length": len(parser.parsed_content),
                "chunks": chunks,
                "chunk_count": len(chunks),
                "strategy": str(strategy)
            }
        except Exception as e:
            return {"error": str(e)}

    def save_to_vector_db(self, chunks: List[str]):
        """
        將分塊存儲至向量數據庫 (待實現)
        """
        pass
