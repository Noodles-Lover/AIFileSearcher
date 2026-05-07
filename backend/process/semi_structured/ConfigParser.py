import os
from typing import Dict, Any
from .SemiStructuredProcessor import SemiStructuredProcessor


class ConfigParser(SemiStructuredProcessor):
    """
    配置/结构化数据文件解析器 (.json, .yaml, .yml, .xml, .toml, .ini, .cfg)
    这类文件分块会破坏结构完整性，使用 LLM 生成语义描述更合适
    """

    type = "config"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(file_path, **kwargs)
        self._config_type: str = ""

    def _extract_content(self) -> str:
        ext = os.path.splitext(self.file_path)[1].lower()
        self._config_type = ext.lstrip(".")

        try:
            if ext == ".json":
                return self._extract_json()
            elif ext in (".yaml", ".yml"):
                return self._extract_yaml()
            elif ext == ".xml":
                return self._extract_xml()
            elif ext == ".toml":
                return self._extract_toml()
            elif ext in (".ini", ".cfg"):
                return self._extract_ini()
            else:
                # 兜底：直接读取文本
                return self._read_raw()
        except Exception as e:
            print(f"❌ 读取配置文件失败 {self.file_path}: {e}")
            return self._read_raw()

    def _read_raw(self) -> str:
        """兜底：直接读取原始文本"""
        encodings = ["utf-8", "gbk", "latin-1"]
        for encoding in encodings:
            try:
                with open(self.file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return ""

    def _extract_json(self) -> str:
        import json

        raw = self._read_raw()
        try:
            obj = json.loads(raw)
            # 格式化输出，限制深度和长度
            formatted = json.dumps(obj, ensure_ascii=False, indent=2)
            if len(formatted) > 3000:
                formatted = formatted[:3000] + "\n... (内容过长已截断)"
            return formatted
        except json.JSONDecodeError:
            return raw

    def _extract_yaml(self) -> str:
        try:
            import yaml
            raw = self._read_raw()
            obj = yaml.safe_load(raw)
            if isinstance(obj, dict):
                # 转为 JSON 格式化输出，更易读
                import json
                formatted = json.dumps(obj, ensure_ascii=False, indent=2)
                if len(formatted) > 3000:
                    formatted = formatted[:3000] + "\n... (内容过长已截断)"
                return formatted
            return raw
        except ImportError:
            return self._read_raw()

    def _extract_xml(self) -> str:
        raw = self._read_raw()
        # 简单清洗：去除多余空白
        import re
        cleaned = re.sub(r">\s+<", ">\n<", raw)
        return cleaned

    def _extract_toml(self) -> str:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return self._read_raw()

        raw = self._read_raw()
        try:
            obj = tomllib.loads(raw)
            import json
            formatted = json.dumps(obj, ensure_ascii=False, indent=2)
            if len(formatted) > 3000:
                formatted = formatted[:3000] + "\n... (内容过长已截断)"
            return formatted
        except Exception:
            return raw

    def _extract_ini(self) -> str:
        import configparser
        config = configparser.ConfigParser()
        try:
            config.read(self.file_path, encoding="utf-8")
        except Exception:
            config.read(self.file_path, encoding="gbk")

        text = []
        for section in config.sections():
            text.append(f"[{section}]")
            for key, value in config.items(section):
                text.append(f"  {key} = {value}")

        return "\n".join(text) if text else self._read_raw()

    def _get_description_prompt(self, content_preview: str) -> str:
        file_name = os.path.basename(self.file_path)

        return f"""根据以下配置文件内容，生成一段用于语义检索的描述文本。

要求：
- 只输出描述文本本身，不要有任何前缀、解释或格式标记
- 说明这是什么系统或应用的什么配置（如：服务器配置、数据库配置）
- 包含配置中的关键设置项和值（如端口号、主机地址）
- 提及配置涉及的服务或模块名称
- 根据配置复杂度灵活调整长度：简单配置简短描述，包含多个模块复杂配置可详细描述

文件名：{file_name}
格式：{self._config_type}

配置内容：
{content_preview}"""

    def _get_fallback_description(self) -> str:
        file_name = os.path.basename(self.file_path)
        parts = [f"{self._config_type} 配置文件 {file_name}"]
        if self._content:
            preview = self._content[:300].replace("\n", " ")
            parts.append(preview)
        return " ".join(parts)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **super().metadata,
            "config_type": self._config_type,
            "parser": "ConfigParser",
        }
