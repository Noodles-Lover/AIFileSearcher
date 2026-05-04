from .TextChunkProcessor import TextChunkProcessor
from .ChunkingStrategy import ChunkingStrategy, SlidingWindowChunking, FixedSizeChunking, ParagraphChunking, SentenceChunking
from .TXTParser import TXTParser
from .PDFParser import PDFParser
from .DocParser import DocParser  # 同时处理 .doc 和 .docx
from .PPTParser import PPTParser
from .MDParser import MDParser
from .ImageParser import ImageParser
from .SubtitleParser import SubtitleParser
from .EmailParser import EmailParser
from .TablePreprocessor import TablePreprocessor
from .MDSemanticChunking import MDSemanticChunking
from .SlideChunking import SlideChunking

__all__ = [
    "TextChunkProcessor",
    "ChunkingStrategy",
    "SlidingWindowChunking",
    "FixedSizeChunking",
    "ParagraphChunking",
    "SentenceChunking",
    "TXTParser",
    "PDFParser",
    "DocParser",
    "PPTParser",
    "MDParser",
    "ImageParser",
    "SubtitleParser",
    "EmailParser",
    "TablePreprocessor",
    "MDSemanticChunking",
    "SlideChunking",
]

# 注册 PARSER_MAPPING
TextChunkProcessor.PARSER_MAPPING.update({
    '.txt': TXTParser,
    '.pdf': PDFParser,
    '.doc': DocParser,
    '.docx': DocParser,
    '.pptx': PPTParser,
    '.ppt': PPTParser,
    '.md': MDParser,
    '.markdown': MDParser,
    '.png': ImageParser,
    '.jpg': ImageParser,
    '.jpeg': ImageParser,
    '.bmp': ImageParser,
    '.gif': ImageParser,
    '.webp': ImageParser,
    # 字幕文件（清洗后分块）
    '.srt': SubtitleParser,
    '.vtt': SubtitleParser,
    # 邮件文件（提取正文后分块）
    '.eml': EmailParser,
})
