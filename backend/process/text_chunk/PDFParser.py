import fitz
from .TextChunkProcessor import TextChunkProcessor


class PDFParser(TextChunkProcessor):
    """
    PDF 文件解析器
    """
    type = 'pdf'

    def _extract_content(self) -> str:
        try:
            pdf_doc: fitz.Document = fitz.open(self.file_path)
            if pdf_doc.needs_pass:
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
