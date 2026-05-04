from .SemiStructuredProcessor import SemiStructuredProcessor
from .ExcelParser import ExcelParser
from .CSVParser import CSVParser
from .DatabaseParser import DatabaseParser
from .JSONLParser import JSONLParser
from .ParquetParser import ParquetParser
from .ConfigParser import ConfigParser
from .CodeParser import CodeParser
from .LogParser import LogParser

__all__ = [
    "SemiStructuredProcessor",
    "ExcelParser",
    "CSVParser",
    "DatabaseParser",
    "JSONLParser",
    "ParquetParser",
    "ConfigParser",
    "CodeParser",
    "LogParser",
]

# 更新 PARSER_MAPPING：将各扩展名映射到对应的解析器
SemiStructuredProcessor.PARSER_MAPPING.update({
    # Excel
    ".xlsx": ExcelParser,
    # CSV / TSV
    ".csv": CSVParser,
    ".tsv": CSVParser,
    # Database
    ".db": DatabaseParser,
    ".sqlite": DatabaseParser,
    ".sqlite3": DatabaseParser,
    # JSON Lines
    ".jsonl": JSONLParser,
    # Parquet / Feather
    ".parquet": ParquetParser,
    ".feather": ParquetParser,
    # 配置/结构化文件
    ".json": ConfigParser,
    ".yaml": ConfigParser,
    ".yml": ConfigParser,
    ".xml": ConfigParser,
    ".toml": ConfigParser,
    ".ini": ConfigParser,
    ".cfg": ConfigParser,
    # 源代码文件
    ".py": CodeParser,
    ".js": CodeParser,
    ".ts": CodeParser,
    ".java": CodeParser,
    ".c": CodeParser,
    ".cpp": CodeParser,
    ".h": CodeParser,
    ".hpp": CodeParser,
    ".go": CodeParser,
    ".rs": CodeParser,
    ".rb": CodeParser,
    ".php": CodeParser,
    ".swift": CodeParser,
    ".kt": CodeParser,
    ".html": CodeParser,
    ".htm": CodeParser,
    ".css": CodeParser,
    ".scss": CodeParser,
    ".sql": CodeParser,
    ".ipynb": CodeParser,
    ".sh": CodeParser,
    ".bash": CodeParser,
    ".zsh": CodeParser,
    ".bat": CodeParser,
    # 日志文件
    ".log": LogParser,
})
