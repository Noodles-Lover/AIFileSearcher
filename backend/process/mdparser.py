from pathlib import Path
from typing import List
from collections import defaultdict
from .parser_base import BaseParser

class MDParser(BaseParser):
    """
    Parser for Markdown files
    """
    type = 'md'
    
    def _extract_content(self) -> str:
        """
        Extract content from MD file
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
            return raw_text
        except Exception as e:
            print(f"Error reading MD file {self.file_path}: {e}")
            return ""

    def _extract_metadata(self) -> defaultdict:
        # TODO: Implement YAML frontmatter extraction if needed
        return defaultdict(str)

    def _check_format(self) -> bool:
        f_path: Path = Path(self.file_path)
        return f_path.exists() and f_path.suffix.lower() == '.md'
