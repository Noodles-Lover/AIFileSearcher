from typing import Dict, Any, Type
from backend.process.BaseFileProcessor import BaseFileProcessor


class SemiStructuredProcessor(BaseFileProcessor):
    """
    半结构化文件处理器
    解析文件内容并使用LLM生成描述
    """

    PARSER_MAPPING: Dict[str, Type["SemiStructuredProcessor"]] = {}

    def __init__(
        self,
        file_path: str,
        vector_store=None,
        embedding_model=None,
        llm_client=None,
    ):
        super().__init__(file_path, vector_store, embedding_model, llm_client)
        self._content: str = ""
        self._description: str = ""

    def get_text(self) -> str:
        self._content = self._extract_content()
        self._metadata = self._get_file_info()
        self._description = self._generate_description()
        return self._description

    def _extract_content(self) -> str:
        return ""

    def _generate_description(self) -> str:
        if not self._content:
            return ""

        if self.llm_client is None:
            return f"文件内容摘要: {self._content[:500]}..."

        prompt = f"""请为以下文件内容生成简短描述（100字以内）：

内容：
{self._content[:2000]}...

请只返回描述文字，不要其他内容。"""

        try:
            response = self.llm_client.query(prompt)
            return response if response else f"文件内容摘要: {self._content[:200]}"
        except Exception as e:
            print(f"LLM描述生成失败: {e}")
            return f"文件内容摘要: {self._content[:200]}"

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._metadata,
            "content_length": len(self._content),
            "description_length": len(self._description),
        }


SemiStructuredProcessor.PARSER_MAPPING.update({
    ext: SemiStructuredProcessor
    for ext in [
        ".xls", ".xlsx", ".ods",
        ".parquet", ".feather",
        ".db", ".sqlite", ".sqlite3",
        ".eml", ".msg",
        ".jsonl",
        ".srt", ".vtt",
    ]
})
