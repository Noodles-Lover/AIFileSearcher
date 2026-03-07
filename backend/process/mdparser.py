from pathlib import Path
from typing import List
from collections import defaultdict
from .BaseParser import BaseParser

class MDParser(BaseParser):
    """
    Markdown 文件解析器
    """
    type = 'md'
    
    def _extract_content(self) -> str:
        """
        提取 Markdown 文件內容
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
            return raw_text
        except Exception as e:
            print(f"Error reading MD file {self.file_path}: {e}")
            return ""

    def _extract_metadata(self) -> defaultdict:
        # 待辦: 如果需要，實現 YAML frontmatter 提取
        return defaultdict(str)

    def _check_format(self) -> bool:
        f_path: Path = Path(self.file_path)
        return f_path.exists() and f_path.suffix.lower() == '.md'
