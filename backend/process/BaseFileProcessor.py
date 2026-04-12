from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Type, Optional
from pathlib import Path
import os


class BaseFileProcessor(ABC):
    """
    文件处理器基类
    包含两种核心方法：
    1. get_text(): 获取解析文本（分块或LLM结果）
    2. vectorize_and_store(): 向量化并存储

    子类通过 PARSER_MAPPING 定义具体文件类型到解析器的映射
    """

    PARSER_MAPPING: Dict[str, Type["BaseFileProcessor"]] = {}

    def __init__(
        self,
        file_path: str,
        vector_store=None,
        embedding_model=None,
        llm_client=None,
    ):
        self.file_path: str = file_path
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.llm_client = llm_client
        self._metadata: Dict[str, Any] = {}

    @abstractmethod
    def get_text(self) -> Union[str, List[str]]:
        pass

    @classmethod
    def get_parser(cls, file_path: str) -> Optional[Type["BaseFileProcessor"]]:
        ext = os.path.splitext(file_path)[1].lower()
        return cls.PARSER_MAPPING.get(ext)

    def vectorize_and_store(self) -> Dict[str, Any]:
        try:
            text = self.get_text()

            if isinstance(text, list):
                texts_to_embed = text
            else:
                texts_to_embed = [text]

            if not texts_to_embed or (len(texts_to_embed) == 1 and not texts_to_embed[0]):
                return {"error": "No text to embed"}

            embeddings = self.embedding_model.encode(texts_to_embed)

            for i, (t, emb) in enumerate(zip(texts_to_embed, embeddings)):
                self.vector_store.add_text(
                    text=t,
                    embedding=emb,
                    metadata={
                        "file_path": self.file_path,
                        "processor": self.__class__.__name__,
                        "index": i,
                        **self._metadata,
                    },
                )

            return {
                "success": True,
                "text_count": len(texts_to_embed),
                "file_path": self.file_path,
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_file_info(self) -> Dict[str, Any]:
        path = Path(self.file_path)
        return {
            "file_name": path.name,
            "file_extension": path.suffix,
            "file_size": os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0,
            "file_path": str(path.absolute()),
        }
