from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict
import sys
import os

from .parser_base import BaseParser

class TXTParser(BaseParser):
    """
    Parser for txt files
    """
    type = 'txt'
    
    def _extract_content(self) -> str:
        """
        Extract content from TXT file
        """
        # Ignore errors from opening 'utf-16' files
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