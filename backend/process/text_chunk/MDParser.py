from pathlib import Path
from .TextChunkProcessor import TextChunkProcessor


class MDParser(TextChunkProcessor):
    """
    Markdown 文件解析器
    """
    type = 'md'

    def _extract_content(self) -> str:
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
            return raw_text
        except Exception as e:
            print(f"Error reading MD file {self.file_path}: {e}")
            return ""
