import pptx
from .TextChunkProcessor import TextChunkProcessor


class PPTParser(TextChunkProcessor):
    """
    PPTX 文件解析器
    """
    type = 'pptx'

    def _extract_content(self) -> str:
        try:
            prs = pptx.Presentation(self.file_path)
            full_text = []

            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        full_text.append(shape.text)

            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading PPTX file {self.file_path}: {e}")
            return ""
