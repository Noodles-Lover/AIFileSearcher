from pathlib import Path
from typing import List, Dict
from collections import defaultdict
import fitz
from .BaseParser import BaseParser

class PDFParser(BaseParser):
    """
    PDF 文件解析器
    """
    type = 'pdf'
    
    def _extract_content(self) -> str:
        """
        使用 PyMuPDF (fitz) 提取 PDF 文件內容
        """
        try:
            pdf_doc: fitz.Document = fitz.open(self.file_path)
            if pdf_doc.needs_pass:
                # 如果 PDF 有密碼保護，跳過
                pdf_doc.close()
                return ""
            
            raw_text = ""
            for page in pdf_doc:
                raw_text += page.get_text("text") + "\n"
            
            pdf_doc.close()
            return raw_text
        except Exception as e:
            print(f"Error reading PDF file {self.file_path}: {e}")
            return ""

    def _extract_metadata(self) -> defaultdict:
        metadata = defaultdict(str)
        try:
            pdf_doc: fitz.Document = fitz.open(self.file_path)
            meta = pdf_doc.metadata
            metadata['title'] = meta.get('title', '')
            metadata['author'] = meta.get('author', '')
            metadata['subject'] = meta.get('subject', '')
            pdf_doc.close()
        except Exception:
            pass
        return metadata

    def _check_format(self) -> bool:
        f_path: Path = Path(self.file_path)
        return f_path.exists() and f_path.suffix.lower() == '.pdf'
