"""评估测试配置"""
import os

# 项目根目录（自动计算）
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# 测试用例 JSON 文件路径
TEST_CASES_FILE = None  # 动态设置

# txt, md, ppt, doc, pdf
CURRENT_TEST_TYPE = "txt"

# ============ 性能测试参数 ============

# 嵌入模型名称（必须与 models/embedding/ 下的目录名一致）
EMBEDDING_MODEL = "bge-m3"

# 嵌入模型路径（自动生成）
EMBEDDING_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "embedding", EMBEDDING_MODEL)

# 索引类型：IndexFlatL2, IndexFlatIP, IndexIVFFlat, IndexHNSWFlat
INDEX_TYPE = "IndexFlatL2"

# 分块策略（直接指定策略类）
# 可选：SlidingWindowChunking, FixedSizeChunking, ParagraphChunking, SentenceChunking
from backend.process.text_chunk.ChunkingStrategy import (
    ChunkingStrategy, SlidingWindowChunking, FixedSizeChunking, 
    ParagraphChunking, SentenceChunking
)
from backend.process.text_chunk.MDSemanticChunking import MDSemanticChunking
from backend.process.text_chunk.SlideChunking import SlideChunking

# 所有要测试的分块策略（遍历时会使用此列表）
ALL_CHUNKING_STRATEGIES = [
    SlidingWindowChunking(chunk_size=500, overlap=50, min_chunk_size=100),
    FixedSizeChunking(chunk_size=500),
    SentenceChunking(max_chars=500),
    ParagraphChunking(lines_per_para=5, min_para_chars=50),
    MDSemanticChunking(max_chunk_size=1200, min_chunk_size=100, max_header_level=3),
    # SlideChunking()
]

# 当前策略（用于单次测试，直接指定一个策略对象）
CHUNKING_STRATEGY = None

# ============ 其他配置 ============

# 是否启用 LLM 重写查询
ENABLE_QUERY_REWRITE = True

# LLM 类型: "deepseek" (API) 或 "local" (本地模型)
LLM_TYPE = "deepseek"


def get_chunking_name():
    """获取分块策略名称"""
    if CHUNKING_STRATEGY is None:
        return "Native"  # 表示使用各文件类型的原生默认策略
    return str(CHUNKING_STRATEGY)
