import os
from collections import defaultdict
from pathlib import Path
from typing import Any, List
from .TextChunkProcessor import TextChunkProcessor


class ImageParser(TextChunkProcessor):
    """
    图片文件解析器
    """
    type = "image"
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
    embedding_mode = "image"

    def _extract_content(self) -> str:
        metadata = self.metadata
        filename = os.path.basename(self.file_path)
        parts = [f"Image file: {filename}"]

        if metadata.get("format"):
            parts.append(f"format={metadata['format']}")
        if metadata.get("width") and metadata.get("height"):
            parts.append(f"size={metadata['width']}x{metadata['height']}")
        if metadata.get("mode"):
            parts.append(f"mode={metadata['mode']}")

        return ", ".join(parts)

    @property
    def metadata(self) -> defaultdict:
        metadata = defaultdict(str)

        try:
            from PIL import Image

            with Image.open(self.file_path) as image:
                metadata["format"] = image.format or ""
                metadata["width"] = image.width
                metadata["height"] = image.height
                metadata["mode"] = image.mode or ""
        except Exception:
            pass

        return metadata

    def get_embedding_inputs(self) -> List[Any]:
        from PIL import Image

        with Image.open(self.file_path) as image:
            return [image.convert("RGB").copy()]
