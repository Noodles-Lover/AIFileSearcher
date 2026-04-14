"""
RAG 检索评估脚本 - 集成 RAGAS 指标

支持：
- 从 JSON 文件加载测试用例
- 灵活配置测试文件类型（txt, md）
- 本地 LLM 模型（Qwen2.5-3B-Instruct）
- LLM 查询重写
- 多种评估指标
"""
import sys
import os
import json

# 添加项目根目录到 path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
os.chdir(project_root)

from backend.utils.path_utils import ensure_project_path, get_data_path
ensure_project_path()

from backend.RAG.EmbeddingModel import EmbeddingModel
from backend.RAG.VectorStore import VectorStore
from backend.utils.IndexedFoldersManager import folders_manager
from backend.utils.search_utils import rewrite_query_with_llm
import numpy as np
import time

# ============================================================
# 配置区域
# ============================================================

# 测试用例 JSON 文件路径
TEST_CASES_FILE = os.path.join(backend_dir, "test", "ragas_test", "test_cases.json")

# 当前测试类型: "txt" 或 "md"
CURRENT_TEST_TYPE = "txt"

# LLM 配置（使用本地模型）
LOCAL_LLM_PATH = os.path.join(project_root, "models", "LLM", "Qwen2.5-3B-Instruct")

# 是否启用 LLM 重写查询
ENABLE_QUERY_REWRITE = True

# LLM 类型: "deepseek" (API) 或 "local" (本地模型)
LLM_TYPE = "deepseek"  # 默认使用 DeepSeek API（速度快，质量好）


# ============================================================
# 加载测试用例
# ============================================================

def load_test_cases(test_type: str) -> dict:
    """从 JSON 文件加载指定类型的测试用例"""
    with open(TEST_CASES_FILE, 'r', encoding='utf-8') as f:
        all_cases = json.load(f)
    return all_cases[test_type]


# ============================================================
# 辅助函数
# ============================================================

def clear_index_files():
    """清空索引文件"""
    index_path = get_data_path("faiss_index.bin")
    metadata_path = get_data_path("metadata.json")
    cache_path = get_data_path("file_cache.json")
    info_path = get_data_path("faiss_index.info")
    
    files_deleted = []
    
    for path, name in [(index_path, "faiss_index.bin"), 
                       (metadata_path, "metadata.json"),
                       (cache_path, "file_cache.json"),
                       (info_path, "faiss_index.info")]:
        if os.path.exists(path):
            try:
                os.remove(path)
                files_deleted.append(name)
            except Exception as e:
                print(f"  Failed to delete {name}: {e}")
    
    folders_manager.clear()
    return files_deleted


def setup_index():
    """初始化索引（直接加载 EmbeddingModel，不触发 SystemManager 自动加载 LLM）"""
    clear_index_files()
    time.sleep(0.5)
    
    # 直接初始化 EmbeddingModel，避免 SystemManager 自动加载 LLM
    print("📊 Loading embedding model: bge-m3...")
    embedder = EmbeddingModel(model_name="bge-m3")
    dimension = embedder.model.get_sentence_embedding_dimension()
    print("✅ Embedding model loaded")
    
    store = VectorStore(
        dimension=dimension,
        index_path=get_data_path("faiss_index.bin"),
        metadata_path=get_data_path("metadata.json")
    )
    
    return embedder, store


def get_files_from_config(test_path: str, test_type: str) -> list:
    """从配置路径获取测试文件"""
    ext = f".{test_type}"
    files = []
    for filename in os.listdir(test_path):
        if filename.endswith(ext):
            files.append(os.path.join(test_path, filename))
    return files


def index_files(store, file_list, embedder):
    """索引文件"""
    vectors = []
    metadata = []
    
    for file_path in file_list:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        vector = embedder.encode([content])[0]
        vectors.append(vector)
        
        filename = os.path.basename(file_path)
        category = extract_category(filename)
        
        metadata.append({
            "file_path": file_path,
            "file_name": filename,
            "content": content,
            "category": category
        })
    
    vectors_array = np.array(vectors).astype('float32')
    store.add(vectors_array, metadata)
    
    return metadata


def extract_category(filename):
    """
    从文件名提取分类
    
    规则（按优先级）：
    1. 下划线 "_" 前的内容
    2. 中横线 "-" 前的内容（当下划线不存在时）
    3. 全文件名（当都没有时）
    
    示例：
      "健康医疗_体检报告.txt" -> "健康医疗"
      "会议纪要_Sprint评审.md" -> "会议纪要"
      "Git教程.md" -> "Git教程"
    """
    # 优先使用下划线
    if '_' in filename:
        return filename.split('_')[0]
    # 其次使用中横线
    if '-' in filename:
        return filename.split('-')[0]
    # 否则使用文件名（去除扩展名）
    return os.path.splitext(filename)[0]


def rewrite_query(query: str, use_deepseek: bool = True) -> str:
    """使用 LLM 重写查询"""
    return rewrite_query_with_llm(query, use_deepseek=use_deepseek)


def evaluate_retrieval(store, embedder, query: str, expected_category: str, 
                       use_rewrite: bool = True) -> dict:
    """
    评估单次检索
    
    Returns:
        dict: {
            "original_query": str,
            "rewritten_query": str or None,
            "results": list,
            "hit": bool,
            "precision_at_1": float,
            "precision_at_3": float,
            "category_hits": dict
        }
    """
    # LLM 重写（可选）
    rewritten = None
    search_query = query
    if use_rewrite:
        use_deepseek = (LLM_TYPE == "deepseek")
        rewritten = rewrite_query(query, use_deepseek=use_deepseek)
        search_query = rewritten
    
    # 向量化查询
    query_vector = embedder.encode([search_query])[0]
    
    # 检索
    results = store.search(query_vector, k=5)
    
    # 检查前1/3个结果中是否有期望分类的文件
    top_1 = results[:1]
    top_3 = results[:3]
    
    p_at_1 = 0.0
    p_at_3 = 0.0
    
    for r in top_1:
        if r.get('category') == expected_category:
            p_at_1 = 1.0
            break
    
    hit_count = 0
    for r in top_3:
        if r.get('category') == expected_category:
            hit_count += 1
    p_at_3 = hit_count / 3.0
    
    return {
        "original_query": query,
        "rewritten_query": rewritten,
        "results": results,
        "hit": p_at_1 > 0 or p_at_3 > 0,
        "precision_at_1": p_at_1,
        "precision_at_3": p_at_3,
        "category_hits": {
            "top1": p_at_1 > 0,
            "top3": hit_count
        }
    }


def print_result(result: dict, index: int = None):
    """打印单个检索结果"""
    prefix = f"[{index}] " if index else ""
    
    print(f"\n{prefix}Query: {result['original_query']}")
    
    if result['rewritten_query']:
        print(f"      [Rewritten]: {result['rewritten_query']}")
    
    print(f"      Expected: {result.get('expected_category', 'N/A')}")
    
    for i, r in enumerate(result['results'][:3]):
        category = r.get('category', 'unknown')
        filename = r.get('file_name', 'unknown')
        score = r.get('score', 0.0)
        match = "✓" if category == result.get('expected_category') else " "
        print(f"      {match} {i+1}. [{category}] {filename} (score: {score:.4f})")


def calculate_metrics(all_results: list) -> dict:
    """计算总体评估指标"""
    n = len(all_results)
    
    p_at_1 = [r['precision_at_1'] for r in all_results]
    p_at_3 = [r['precision_at_3'] for r in all_results]
    
    # MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for r in all_results:
        # 找到第一个命中的位置
        for i, res in enumerate(r['results']):
            if res.get('category') == r.get('expected_category'):
                mrr += 1.0 / (i + 1)
                break
    
    # Hit Rate@3
    hit_at_3 = sum(1 for r in all_results if r['category_hits']['top3'] > 0)
    
    return {
        "precision_at_1": np.mean(p_at_1),
        "precision_at_3": np.mean(p_at_3),
        "mrr": mrr / n if n > 0 else 0.0,
        "hit_rate_at_3": hit_at_3 / n if n > 0 else 0.0,
        "total": n,
        "hits": sum(1 for r in all_results if r['hit'])
    }


def print_metrics(metrics: dict):
    """打印评估指标"""
    print("\n" + "=" * 50)
    print("EVALUATION METRICS")
    print("=" * 50)
    print(f"Total queries:       {metrics['total']}")
    print(f"Hits (top-3):        {metrics['hits']}/{metrics['total']}")
    print(f"Precision@1:        {metrics['precision_at_1']:.4f}")
    print(f"Precision@3:        {metrics['precision_at_3']:.4f}")
    print(f"MRR:                {metrics['mrr']:.4f}")
    print(f"Hit Rate@3:         {metrics['hit_rate_at_3']:.4f}")
    print("=" * 50)


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("AIFileSearcher Retrieval Evaluation")
    print("=" * 60)
    
    # 加载测试用例
    print(f"\n[Config] Loading test cases from: {TEST_CASES_FILE}")
    print(f"[Config] Test type: {CURRENT_TEST_TYPE}")
    print(f"[Config] LLM Rewrite: {'Enabled' if ENABLE_QUERY_REWRITE else 'Disabled'}")
    print(f"[Config] LLM Type: {LLM_TYPE}")
    
    test_cases = load_test_cases(CURRENT_TEST_TYPE)
    test_queries = test_cases["queries"]
    test_path = test_cases["path"]
    
    print(f"[Config] Test path: {test_path}")
    print(f"[Config] Queries: {len(test_queries)}")
    
    # Step 1: 清空索引
    print("\n[Step 1] Clearing index...")
    deleted = clear_index_files()
    print(f"[Step 1] Deleted files: {deleted}")
    
    # Step 2: 初始化索引
    print("\n[Step 2] Initializing index...")
    embedder, store = setup_index()
    
    # Step 3: 索引测试文件
    print("\n[Step 3] Indexing test files...")
    files = get_files_from_config(test_path, CURRENT_TEST_TYPE)
    print(f"[Step 3] Found {len(files)} files")
    
    metadata = index_files(store, files, embedder)
    print(f"[Step 3] Indexed {len(metadata)} files")
    
    # Step 4: 评估检索
    print(f"\n[Step 4] Evaluating retrieval...")
    print(f"[Step 4] Running {len(test_queries)} queries...\n")
    
    all_results = []
    
    for i, q in enumerate(test_queries):
        query = q["query"]
        expected = q["expected_category"]
        
        result = evaluate_retrieval(
            store=store,
            embedder=embedder,
            query=query,
            expected_category=expected,
            use_rewrite=ENABLE_QUERY_REWRITE
        )
        result["expected_category"] = expected
        all_results.append(result)
        
        print_result(result, i + 1)
    
    # Step 5: 计算并打印指标
    metrics = calculate_metrics(all_results)
    print_metrics(metrics)
    
    print("\n[Done] Evaluation complete!")


if __name__ == "__main__":
    main()
