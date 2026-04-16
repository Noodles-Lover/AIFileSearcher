from pathlib import Path
from .TextChunkProcessor import TextChunkProcessor
from .TablePreprocessor import TablePreprocessor


class MDParser(TextChunkProcessor):
    """
    Markdown 文件解析器
    默认使用 MDSemanticChunking（按标题层级分块）
    """
    type = 'md'

    def _extract_content(self) -> str:
        """提取 Markdown 内容"""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 预处理：标准化表格格式
            return TablePreprocessor.preprocess(content)
        except Exception as e:
            print(f"Error reading MD file {self.file_path}: {e}")
            return ""
