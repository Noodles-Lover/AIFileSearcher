import docx
from .TextChunkProcessor import TextChunkProcessor


class DocxParser(TextChunkProcessor):
    """
    DOCX 文件解析器
    """
    type = 'docx'

    def _extract_content(self) -> str:
        try:
            doc = docx.Document(self.file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading DOCX file {self.file_path}: {e}")
            return ""
