from collections import defaultdict
from typing import List, Any, Optional, Dict
from abc import ABC, abstractmethod
from .chunking import ChunkingStrategy

class BaseParser(ABC):
    """
    Data Parser Base Class
    Implements Template Method Pattern for parsing logic
    Implements Strategy Pattern for chunking logic
    """
    type = None
    
    def __init__(self, file_path: str, chunking_strategy: ChunkingStrategy = None) -> None:
        self.file_path: str = file_path
        self.chunking_strategy: ChunkingStrategy = chunking_strategy
        self._metadata: Optional[defaultdict] = None
        self.parsed_content: str = ""
        self.chunks: List[str] = []

    def set_chunking_strategy(self, strategy: ChunkingStrategy):
        """
        Dynamically update chunking strategy
        """
        self.chunking_strategy = strategy

    def process(self) -> List[str]:
        """
        Template Method: Defines the skeleton of the parsing algorithm
        1. Check Format
        2. Extract Content (Abstract)
        3. Clean Content (Abstract/Optional)
        4. Chunk Content (Strategy)
        """
        if not self._check_format():
            raise ValueError(f"Invalid file format for {self.file_path}")

        # Step 1: Extract Raw Content
        self.parsed_content = self._extract_content()
        if not self.parsed_content:
            return []

        # Step 2: Clean/Preprocess Content
        self.parsed_content = self._clean_content(self.parsed_content)

        # Step 3: Chunk Content using Strategy
        if self.chunking_strategy:
            self.chunks = self.chunking_strategy.chunk(self.parsed_content)
        else:
            # Default behavior if no strategy provided: return whole content as one chunk
            self.chunks = [self.parsed_content]
            
        return self.chunks

    @abstractmethod
    def _extract_content(self) -> str:
        """
        Abstract method to extract raw text from file
        Must be implemented by concrete parsers (TXT, PDF, etc.)
        """
        pass

    def _clean_content(self, text: str) -> str:
        """
        Hook method for cleaning text (optional override)
        """
        # Default implementation: simple whitespace normalization
        return text.strip()

    @abstractmethod
    def _check_format(self) -> bool:
        """
        Check input file format
        """
        pass
    
    @property
    def metadata(self) -> defaultdict:
        """
        Get metadata (lazy load)
        """
        if self._metadata is None:
            self._metadata = self._extract_metadata()
        return self._metadata

    def _extract_metadata(self) -> defaultdict:
        """
        Abstract method to extract metadata
        """
        return defaultdict(str)