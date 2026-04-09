from pathlib import Path
from typing import Any, List
from .BaseParser import BaseParser
from .PDFParser import PDFParser
from .DocxParser import DocxParser
from .PPTParser import PPTParser
from .MDParser import MDParser
from .ImageParser import ImageParser
from .TXTParser import TXTParser
from .FileProcessor import FileProcessor

parsers: List[BaseParser] = [PDFParser, TXTParser, DocxParser, PPTParser, MDParser, ImageParser]


def _get_parser(suffix: str) -> BaseParser:
    for parser in parsers:
        if parser.type.lower() == suffix.lower():
            return parser
    return None
    
def get_valid_file_suffixes():
    suffixes = []
    for parser in parsers:
        suffixes.append(parser.type.lower())
    return suffixes
