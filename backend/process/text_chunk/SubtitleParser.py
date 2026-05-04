import os
import re
from typing import Dict, Any
from .TextChunkProcessor import TextChunkProcessor


class SubtitleParser(TextChunkProcessor):
    """
    字幕文件解析器 (.srt, .vtt)
    清洗时间码和序号，提取纯文本后分块
    """

    type = "subtitle"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._subtitle_count: int = 0
        self._duration: str = ""
        self._format: str = ""

    def _extract_content(self) -> str:
        ext = os.path.splitext(self.file_path)[1].lower()
        self._format = ext.lstrip(".")

        try:
            encodings = ["utf-8", "gbk", "latin-1"]
            raw_text = ""

            for encoding in encodings:
                try:
                    with open(self.file_path, "r", encoding=encoding) as f:
                        raw_text = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if not raw_text.strip():
                return ""

            if ext == ".srt":
                return self._parse_srt(raw_text)
            elif ext == ".vtt":
                return self._parse_vtt(raw_text)
            else:
                return raw_text

        except Exception as e:
            print(f"❌ 读取字幕文件失败 {self.file_path}: {e}")
            return ""

    def _parse_srt(self, text: str) -> str:
        """解析 SRT 格式，清洗时间码和序号，只保留字幕文本"""
        lines = []
        blocks = re.split(r"\n\s*\n", text.strip())

        last_end_time = ""
        for block in blocks:
            block_lines = block.strip().split("\n")
            if len(block_lines) >= 2:
                # 检测时间码行
                time_match = re.match(
                    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})",
                    block_lines[1].strip()
                )
                if time_match:
                    last_end_time = time_match.group(2)
                    self._subtitle_count += 1

                # 提取字幕文本（跳过序号和时间码行）
                subtitle_text = "\n".join(block_lines[2:]).strip()
                if subtitle_text:
                    subtitle_text = re.sub(r"<[^>]+>", "", subtitle_text)
                    lines.append(subtitle_text)

        self._duration = last_end_time
        return "\n".join(lines)

    def _parse_vtt(self, text: str) -> str:
        """解析 WebVTT 格式，清洗时间码，只保留字幕文本"""
        lines = []
        text = re.sub(r"^WEBVTT.*\n", "", text, flags=re.IGNORECASE)
        blocks = re.split(r"\n\s*\n", text.strip())

        last_end_time = ""
        for block in blocks:
            block_lines = block.strip().split("\n")
            # 查找时间码行
            time_line_idx = -1
            for i, line in enumerate(block_lines):
                if re.match(r"\d{2}:\d{2}", line.strip()):
                    time_line_idx = i
                    break

            if time_line_idx >= 0:
                time_match = re.search(
                    r"(\d{2}:\d{2}(?::\d{2})?[.,]\d{3})\s*-->\s*(\d{2}:\d{2}(?::\d{2})?[.,]\d{3})",
                    block_lines[time_line_idx]
                )
                if time_match:
                    last_end_time = time_match.group(2)
                    self._subtitle_count += 1

                # 提取字幕文本
                subtitle_text = "\n".join(block_lines[time_line_idx + 1:]).strip()
                if subtitle_text:
                    subtitle_text = re.sub(r"<[^>]+>", "", subtitle_text)
                    lines.append(subtitle_text)

        self._duration = last_end_time
        return "\n".join(lines)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._metadata,
            "subtitle_count": self._subtitle_count,
            "duration": self._duration,
            "format": self._format,
            "content_length": len(self._parsed_content),
            "chunk_count": len(self._chunks),
        }
