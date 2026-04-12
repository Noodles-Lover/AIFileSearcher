import subprocess
import os
from .TextChunkProcessor import TextChunkProcessor

HAS_EXTRACTOR = False
try:
    import textract
    HAS_EXTRACTOR = True
except ImportError:
    print("Warning: textract not installed, trying alternative methods for .doc files")

HAS_WIN32COM = False
try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    print("Warning: win32com not installed, .doc files may not be supported")


class DocParser(TextChunkProcessor):
    """
    DOC 文件解析器
    """
    type = 'doc'

    def _extract_content(self) -> str:
        if HAS_EXTRACTOR:
            try:
                text = textract.process(self.file_path, encoding='utf-8').decode('utf-8')
                return text.strip()
            except Exception as e:
                print(f"Error using textract for {self.file_path}: {e}")
                if HAS_WIN32COM:
                    return self._extract_with_win32com()
                else:
                    return ""
        elif HAS_WIN32COM:
            return self._extract_with_win32com()
        else:
            print("Error: No .doc file extractor available")
            return ""

    def _extract_with_win32com(self) -> str:
        try:
            word = win32com.client.Dispatch('Word.Application')
            word.Visible = False
            doc = word.Documents.Open(self.file_path)
            full_text = []

            for para in doc.Paragraphs:
                text = para.Range.Text.strip()
                if text:
                    full_text.append(text)

            doc.Close(False)
            word.Quit()

            return '\n'.join(full_text)
        except Exception as e:
            print(f"Error reading DOC file {self.file_path}: {e}")
            try:
                word.Quit()
            except:
                pass
            return ""
