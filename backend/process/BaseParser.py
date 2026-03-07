from collections import defaultdict
from typing import List, Any, Optional, Dict
from abc import ABC, abstractmethod
from .ChunkingStrategy import ChunkingStrategy

class BaseParser(ABC):
    """
    數據解析器基類
    實現了解析邏輯的模板方法模式 (Template Method Pattern)
    實現了分塊邏輯的策略模式 (Strategy Pattern)
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
        動態更新分塊策略
        """
        self.chunking_strategy = strategy

    def process(self) -> List[str]:
        """
        模板方法：定義解析算法的骨架
        1. 檢查格式
        2. 提取內容 (抽象)
        3. 清洗內容 (抽象/可選)
        4. 內容分塊 (策略)
        """
        if not self._check_format():
            raise ValueError(f"Invalid file format for {self.file_path}")

        # 步驟 1: 提取原始內容
        self.parsed_content = self._extract_content()
        if not self.parsed_content:
            return []

        # 步驟 2: 清洗/預處理內容
        self.parsed_content = self._clean_content(self.parsed_content)

        # 步驟 3: 使用策略進行分塊
        if self.chunking_strategy:
            self.chunks = self.chunking_strategy.chunk(self.parsed_content)
        else:
            # 如果未提供策略，默認行爲：將整個內容作爲一個塊返回
            self.chunks = [self.parsed_content]
            
        return self.chunks

    @abstractmethod
    def _extract_content(self) -> str:
        """
        提取文件原始文本的抽象方法
        必須由具體解析器 (TXT, PDF 等) 實現
        """
        pass

    def _clean_content(self, text: str) -> str:
        """
        清洗文本的鉤子方法 (可選覆蓋)
        """
        # 默認實現：簡單的空白字符標準化
        return text.strip()

    @abstractmethod
    def _check_format(self) -> bool:
        """
        檢查輸入文件格式
        """
        pass
    
    @property
    def metadata(self) -> defaultdict:
        """
        獲取元數據 (懶加載)
        """
        if self._metadata is None:
            self._metadata = self._extract_metadata()
        return self._metadata

    def _extract_metadata(self) -> defaultdict:
        """
        提取元數據的抽象方法
        """
        return defaultdict(str)