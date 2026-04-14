from typing import Dict, Any, Type
from pathlib import Path
from backend.process.BaseFileProcessor import BaseFileProcessor


class BinaryProcessor(BaseFileProcessor):
    """
    二进制文件处理器
    基于文件名和文件目录结构，使用LLM生成文件功能描述
    """

    PARSER_MAPPING: Dict[str, Type["BinaryProcessor"]] = {}

    def __init__(
        self,
        file_path: str,
        vector_store=None,
        embedding_model=None,
        llm_client=None,
    ):
        super().__init__(file_path, vector_store, embedding_model, llm_client)
        self._structure_info: Dict[str, Any] = {}
        self._description: str = ""

    def get_text(self) -> str:
        self._metadata = self._get_file_info()
        self._structure_info = self._analyze_structure()
        self._description = self._generate_description()
        return self._description

    def _analyze_structure(self) -> Dict[str, Any]:
        path = Path(self.file_path)

        structure = {
            "file_name": path.stem,
            "file_type": path.suffix,
            "locate_dir": path.parent.name,
        }

        try:
            siblings = [p.name for p in path.parent.iterdir() if p.is_file() and p != path]
            structure["sibling_files"] = siblings[:10]
        except:
            pass

        return structure

    def _generate_description(self) -> str:
        from backend.RAG.SystemManager import SystemManager

        structure = self._structure_info
        file_name = structure.get("file_name", "")
        default_description = f"{file_name} {structure.get('file_type', '')}"

        sibling_info = ""
        if structure.get("sibling_files"):
            sibling_info = f"\n同目录文件: {', '.join(structure['sibling_files'][:5])}"

        prompt = f"""
你是一个专业的文件分析助手。请根据文件信息，为该文件生成一段简洁、信息丰富、便于后续向量检索的文本说明。

【任务要求】
1. 说明该文件的可能用途、来源或所属软件系统。
2. 如果是可执行文件（.exe/.dll/.bin），请说明可能的功能模块（如：安装程序、工具、服务、库、驱动等）。
3. 如果是压缩包（.zip/.rar/.7z），请基于文件名和上下文推测可能包含的内容类型（如：文档、代码、资源包、备份等）。
4. 结合同级文件信息，判断该文件在项目或目录结构中的角色（例如：主程序、依赖库、配置文件等）。
5. 描述长度控制在 80~150 字之间，便于向量化。
6. 输出只包含描述文本，不要有多余的解释或格式。

【文件信息】
文件名：{file_name}
文件类型：{structure.get('file_type', '未知')}
绝对路径：{self.file_path}
所在目录：{structure.get('locate_dir', '未知')}{sibling_info}"""
        try:
            sm = SystemManager.get_instance()
            response = sm.generate_with_llm(prompt)
            print(f"* LLM回复: {response}")
            return response if response else default_description
        except Exception as e:
            print(f"LLM描述生成失败: {e}")
            return default_description

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._metadata,
            "structure_info": self._structure_info,
        }


BinaryProcessor.PARSER_MAPPING.update({
    ext: BinaryProcessor
    for ext in [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
        ".exe", ".msi", ".bin", ".apk", ".ipa", ".app",
        ".dll", ".so", ".dylib", ".sys",
        ".iso", ".img", ".dmg", ".vhd", ".vhdx",
        ".ttf", ".otf", ".woff", ".woff2",
        ".class", ".pyc", ".o", ".obj", ".a", ".lib",
        ".pem", ".key", ".crt", ".p12",
        ".dump", ".dmp", ".core",
    ]
})
