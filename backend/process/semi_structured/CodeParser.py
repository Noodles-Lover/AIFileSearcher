import os
from typing import Dict, Any
from .SemiStructuredProcessor import SemiStructuredProcessor


class CodeParser(SemiStructuredProcessor):
    """
    源代码文件解析器 (.py, .js, .ts, .java, .c, .cpp, .h, .hpp, .go, .rs, .rb, .php, .swift, .kt, .html, .htm, .css, .scss, .sql, .ipynb, .sh, .bash, .zsh, .bat)
    源代码文件分块会破坏语义完整性，使用 LLM 生成整体描述更合适
    """

    type = "code"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._language: str = ""

    # 扩展名 → 语言名称映射
    EXT_LANG_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sql": "SQL",
        ".ipynb": "Jupyter Notebook",
        ".sh": "Shell",
        ".bash": "Bash",
        ".zsh": "Zsh",
        ".bat": "Batch",
    }

    def _extract_content(self) -> str:
        ext = os.path.splitext(self.file_path)[1].lower()
        self._language = self.EXT_LANG_MAP.get(ext, "Unknown")

        if ext == ".ipynb":
            return self._extract_notebook()
        else:
            return self._read_raw()

    def _read_raw(self) -> str:
        """读取源代码原始文本"""
        encodings = ["utf-8", "gbk", "latin-1"]
        for encoding in encodings:
            try:
                with open(self.file_path, "r", encoding=encoding) as f:
                    content = f.read()
                if len(content) > 5000:
                    content = content[:5000] + "\n... (内容过长已截断)"
                return content
            except UnicodeDecodeError:
                continue
        return ""

    def _extract_notebook(self) -> str:
        """提取 Jupyter Notebook 内容"""
        import json

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                nb = json.load(f)

            parts = []
            # 提取 notebook 元数据
            if "metadata" in nb:
                kernelspec = nb["metadata"].get("kernelspec", {})
                if kernelspec:
                    parts.append(f"Kernel: {kernelspec.get('display_name', 'unknown')}")

            # 提取各 cell 内容
            for i, cell in enumerate(nb.get("cells", [])):
                cell_type = cell.get("cell_type", "")
                source = "".join(cell.get("source", []))
                if source.strip():
                    parts.append(f"[{cell_type}] {source}")

            content = "\n".join(parts)
            if len(content) > 5000:
                content = content[:5000] + "\n... (内容过长已截断)"
            return content
        except Exception as e:
            print(f"读取 Notebook 失败 {self.file_path}: {e}")
            return self._read_raw()

    def _get_description_prompt(self, content_preview: str) -> str:
        file_name = os.path.basename(self.file_path)

        return f"""请用自然语言描述以下源代码文件，描述将用于语义检索，请包含用户可能搜索的关键信息。

要求：
- 说明这是什么语言、什么功能的代码（如：Python数据处理模块、Go HTTP服务、React组件等）
- 包含代码中出现的类名、函数名、模块名、变量名（这些是用户搜索时会用的词）
- 提及代码依赖的库、框架或包
- 提及代码处理的业务领域或具体功能
- 用你向别人介绍这个代码文件时会用的自然语言来写

文件名：{file_name}
语言：{self._language}

代码内容：
{content_preview}"""

    def _get_fallback_description(self) -> str:
        file_name = os.path.basename(self.file_path)
        parts = [f"{self._language} 代码文件 {file_name}"]
        if self._content:
            preview = self._content[:300].replace("\n", " ")
            parts.append(preview)
        return " ".join(parts)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **super().metadata,
            "language": self._language,
            "parser": "CodeParser",
        }
