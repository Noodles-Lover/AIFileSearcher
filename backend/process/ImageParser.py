import os
from collections import defaultdict
from pathlib import Path
from typing import Any, List

from .BaseParser import BaseParser


class ImageParser(BaseParser):
    """
    Parser for image files.

    It produces a single summary chunk for display/preview and exposes the
    original image as embedding input for the indexing pipeline.
    """

    type = "image"
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
    embedding_mode = "image"

    def process(self) -> List[str]:
        if not self._check_format():
            raise ValueError(f"Invalid file format for {self.file_path}")

        self.parsed_content = self._clean_content(self._extract_content())
        self.chunks = [self.parsed_content] if self.parsed_content else []
        return self.chunks

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

    def _extract_metadata(self) -> defaultdict:
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

    def _check_format(self) -> bool:
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            return False

        file_path = Path(self.file_path)
        return file_path.exists() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
