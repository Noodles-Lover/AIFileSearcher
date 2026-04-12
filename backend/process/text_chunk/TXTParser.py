from .TextChunkProcessor import TextChunkProcessor


class TXTParser(TextChunkProcessor):
    """
    TXT 文件解析器
    """
    type = 'txt'

    def _extract_content(self) -> str:
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
            return raw_text
        except Exception as e:
            print(f"Error reading TXT file {self.file_path}: {e}")
            return ""
