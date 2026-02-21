from pathlib import Path
from typing import List, Dict
from collections import defaultdict
import fitz
from .parser_base import BaseParser

class PDFParser(BaseParser):
    """
    Parser for PDF files
    """
    type = 'pdf'
    
    def _extract_content(self) -> str:
        """
        Extract content from PDF file using PyMuPDF (fitz)
        """
        try:
            pdf_doc: fitz.Document = fitz.open(self.file_path)
            if pdf_doc.needs_pass:
                # If PDF is password protected, skip
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