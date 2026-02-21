from pathlib import Path
from typing import Any, List
from .parser_base import BaseParser
from .pdfparser import PDFParser
from .docxparser import DocxParser
from .pptxparser import PPTParser
from .mdparser import MDParser
from .txtparser import TXTParser

parsers: List[BaseParser] = [PDFParser, TXTParser, DocxParser, PPTParser, MDParser]


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
