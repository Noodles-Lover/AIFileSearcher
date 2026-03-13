from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict
import sys
import os

from .BaseParser import BaseParser

class TXTParser(BaseParser):
    """
    TXT 文件解析器
    """
    type = 'txt'
    
    def _extract_content(self) -> str:
        """
        提取 TXT 文件內容
        """
        # 忽略 'utf-16' 文件打開錯誤
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
            return raw_text
        except Exception as e:
            print(f"Error reading TXT file {self.file_path}: {e}")
            return ""

    def _check_format(self) -> bool:
        f_path: Path = Path(self.file_path)
        return f_path.exists() and f_path.suffix.lower() == '.txt'
