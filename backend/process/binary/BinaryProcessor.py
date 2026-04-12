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
### 角色定义
你是一个专家级文件语义提取器。你的任务是根据文件名、路径和类型，结合你庞大的软件库知识，为无法解析内容的二进制文件生成极其精准的语义向量标签。

### 核心逻辑
1. **知识对齐**：如果文件名对应已知的商业软件、开源项目、驱动程序或系统组件，请直接输出其真实功能（如 AweSun -> 远程控制）。
2. **多维建模**：
   - 实体：软件名、厂商、项目名。
   - 分类：驱动、安装包、固件、游戏、生产力工具等。
   - 功能场景：录制、加密、渲染、底层通信等。
3. **安全边界**：对于完全随机乱码的文件名，仅输出文件类别，不编造功能。

### 约束条件
* 输出格式：仅输出关键词/短语，空格分隔。
* 严禁无意义词：文件、可能、这是。
* 数量要求：4-8个高价值标签。可以在此基础上添加同义、近义词等。

### 示例增强
输入：AweSun_1.5.2.exe
输出：AweSun 远程桌面 远程控制 办公协作 安装包 软件

输入：537.42-desktop-win10-win11-64bit-international-dch-whql.exe
输出：NVIDIA GeForce 显卡驱动 GPU驱动程序 硬件支持 系统工具 安装包

输入：jdk-17_windows-x64_bin.exe
输出：Java JDK 17 Java开发工具包 编程环境 Oracle 软件部署

### 输入
文件信息：
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
