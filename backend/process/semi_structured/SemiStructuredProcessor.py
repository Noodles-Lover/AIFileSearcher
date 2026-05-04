import os
from typing import Dict, Any, Type
from backend.process.BaseFileProcessor import BaseFileProcessor


class SemiStructuredProcessor(BaseFileProcessor):
    """
    半结构化文件处理器基类
    解析文件内容并使用LLM生成描述

    子类需要实现：
    - _extract_content(): 提取文件原始文本内容
    - _get_description_prompt(): 返回用于LLM生成描述的提示词模板

    LLM调用和降级逻辑由父类统一处理
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
        """子类实现：提取文件原始文本内容"""
        return ""

    def _get_description_prompt(self, content_preview: str) -> str:
        """
        子类实现：返回用于LLM生成描述的提示词

        Args:
            content_preview: 文件内容预览（已截断）

        Returns:
            完整的提示词字符串
        """
        file_name = os.path.basename(self.file_path)
        return f"""请为以下文件内容生成简短描述（100字以内）：

文件名：{file_name}

内容：
{content_preview}

请只返回描述文字，不要其他内容。"""

    def _get_fallback_description(self) -> str:
        """
        子类可选重写：LLM不可用或失败时的降级描述
        """
        file_name = os.path.basename(self.file_path)
        if self._content:
            preview = self._content[:300].replace("\n", " ")
            return f"{file_name} {preview}"
        return f"{file_name}"

    def _generate_description(self) -> str:
        """统一调用LLM生成描述，子类不应重写此方法"""
        if not self._content:
            return self._get_fallback_description()

        content_preview = self._content[:2000]
        prompt = self._get_description_prompt(content_preview)

        # 尝试通过 llm_client 调用
        if self.llm_client is not None:
            try:
                response = self.llm_client.query(prompt)
                if response:
                    return response
            except Exception as e:
                print(f"LLM描述生成失败(llm_client): {e}")

        # 尝试通过 SystemManager 调用
        try:
            from backend.RAG.SystemManager import SystemManager
            sm = SystemManager.get_instance()
            response = sm.generate_with_llm(prompt)
            if response:
                return response
        except Exception as e:
            print(f"LLM描述生成失败(SystemManager): {e}")

        # 降级方案
        return self._get_fallback_description()

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._metadata,
            "content_length": len(self._content),
            "description_length": len(self._description),
        }


# PARSER_MAPPING 由 __init__.py 统一注册子类映射
