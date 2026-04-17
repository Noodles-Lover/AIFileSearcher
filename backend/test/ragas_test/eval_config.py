"""评估测试配置"""
import os

# ============ 路径配置 ============
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# 测试用例 JSON 文件路径（动态设置）
TEST_CASES_FILE = None

# 测试文件类型: txt, md, ppt, doc, pdf, many_txt, mixed
CURRENT_TEST_TYPE = "mixed"


# ============ 分块策略导入 ============
from backend.process.text_chunk.ChunkingStrategy import (
    ChunkingStrategy, SlidingWindowChunking, FixedSizeChunking,
    ParagraphChunking, SentenceChunking
)
from backend.process.text_chunk.MDSemanticChunking import MDSemanticChunking
from backend.process.text_chunk.SlideChunking import SlideChunking


# ============ 遍历配置 ============
# 配置说明：
# - 每个列表放一项则执行一次，放多项则遍历测试
# - 设为 None 则跳过该项，使用默认值
# - 三者组合测试：当前配置会测试 5个索引类型 × 1个分块策略 × 1个嵌入模型 = 5 次

# 所有要测试的嵌入模型（与 models/embedding/ 下的目录名一致）
ALL_EMBEDDING_MODELS = [
    # "bge-m3",
    # "Qwen3-Embedding-0.6B",
    # "bge-large-zh-v1.5",
    # "bge-base-zh-v1.5",
    "m3e-base",
    # "bge-small-zh-v1.5"
]

# 所有要测试的索引类型
ALL_INDEX_TYPES = [
    "IndexFlatL2",
    "IndexFlatIP",
    "IndexIVFFlat",
    "IndexHNSWFlat",
    "IndexLSH",
]

# 所有要测试的分块策略（None = 使用各文件类型的原生默认策略）
# 注意：当 ALL_CHUNKING_STRATEGIES 非空时，会对所有文件使用同一策略，
#      若要按文件类型使用不同策略，请设为 None
ALL_CHUNKING_STRATEGIES = None  # 使用 DEFAULT_STRATEGIES（按扩展名分配策略）
# ALL_CHUNKING_STRATEGIES = [SentenceChunking(max_chars=500)]  # 取消注释则对所有文件使用同一策略


# ============ 其他配置 ============
# 是否启用 LLM 重写查询
ENABLE_QUERY_REWRITE = True

# LLM 类型: "deepseek" (API) 或 "local" (本地模型)
LLM_TYPE = "deepseek"


# ============ 辅助函数 ============
def get_strategy_name(strategy):
    """获取分块策略名称"""
    if strategy is None:
        return "Native"
    return str(strategy)


def get_model_path(model_name):
    """获取嵌入模型路径"""
    return os.path.join(PROJECT_ROOT, "models", "embedding", model_name)
