"""RAG 检索评估脚本主流程"""

import sys
import os
import json
import time

# 添加项目根目录到 path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
os.chdir(project_root)

from backend.utils.path_utils import ensure_project_path, get_data_path
ensure_project_path()

from backend.RAG.EmbeddingModel import EmbeddingModel
from backend.RAG.VectorStore import VectorStore
from backend.process.FileProcessor import FileProcessor
from backend.utils.IndexedFoldersManager import folders_manager
from backend.utils.search_utils import rewrite_query_with_llm
import numpy as np

# 导入配置和工具
from eval_config import (
    CURRENT_TEST_TYPE,
    ALL_EMBEDDING_MODELS, ALL_INDEX_TYPES, ALL_CHUNKING_STRATEGIES,
    ENABLE_QUERY_REWRITE, LLM_TYPE, PROJECT_ROOT,
    get_strategy_name, get_model_path
)
from eval_reporter import EvalReporter

# 设置测试用例文件路径
from eval_config import TEST_CASES_FILE as _orig_tcf
if _orig_tcf is None:
    TEST_CASES_FILE = os.path.join(backend_dir, "test", "ragas_test", "test_cases.json")
else:
    TEST_CASES_FILE = _orig_tcf

# 内存监控
import tracemalloc


def get_model_folder_size(model_path: str) -> int:
    """计算模型文件夹总大小（字节）"""
    total_size = 0
    if os.path.exists(model_path):
        for dirpath, dirnames, filenames in os.walk(model_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
    return total_size


def snapshot_memory() -> dict:
    """获取内存快照"""
    current, peak = tracemalloc.get_traced_memory()
    return {
        "current_mb": round(current / (1024 * 1024), 2),
        "peak_mb": round(peak / (1024 * 1024), 2)
    }


# ============================================================
# 辅助函数
# ============================================================

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def get_index_size() -> int:
    """获取索引文件夹的总大小（字节）"""
    data_path = get_data_path("")
    total_size = 0
    
    for filename in ["faiss_index.bin", "metadata.json", "file_cache.json", "faiss_index.info"]:
        filepath = os.path.join(data_path, filename)
        if os.path.exists(filepath):
            total_size += os.path.getsize(filepath)
    
    return total_size


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


def setup_index(index_type, embedding_model):
    """初始化索引
    
    Args:
        index_type: 索引类型
        embedding_model: 嵌入模型名称
    """
    clear_index_files()
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("Loading embedding model...")
    print("=" * 60)
    
    model_load_start = time.time()
    embedder = EmbeddingModel(model_name=embedding_model)
    model_load_time = time.time() - model_load_start
    
    dimension = embedder.model.get_sentence_embedding_dimension()
    model_path = get_model_path(embedding_model)
    
    print(f"\n✅ Embedding model loaded")
    print(f"   Model: {embedding_model}")
    print(f"   Dimension: {dimension}")
    print(f"   Load time: {model_load_time:.2f}s")
    
    print(f"\n📊 Creating index: {index_type}")
    store = VectorStore(
        dimension=dimension,
        index_path=get_data_path("faiss_index.bin"),
        metadata_path=get_data_path("metadata.json"),
        index_type=index_type
    )
    
    print(f"   Index type: {type(store.index).__name__}")
    
    return embedder, store, model_load_time, model_path


# 文件扩展名映射（test_type -> 实际扩展名）
FILE_EXTENSIONS = {
    "doc": [".doc", ".docx"],
    "ppt": [".ppt", ".pptx"],
    "xls": [".xls", ".xlsx"],
    "pdf": [".pdf"],
    "md": [".md"],
    "txt": [".txt"],
    "many_txt": [".txt"],  # 大量 txt 文件测试
    "mixed": [".txt", ".md", ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"],  # 混合文件类型
}


def get_files_from_config(test_path: str, test_type: str) -> list:
    """从配置路径获取测试文件"""
    extensions = FILE_EXTENSIONS.get(test_type, [f".{test_type}"])
    files = []
    for filename in os.listdir(test_path):
        if any(filename.lower().endswith(ext) for ext in extensions):
            files.append(os.path.join(test_path, filename))
    return files


def index_files_with_timing(store, file_list, embedder, processor):
    """索引文件（带性能计时）"""
    all_metadata = []
    total_chunk_time = 0
    total_vector_time = 0
    total_chunks = 0
    per_file_stats = []
    
    for i, file_path in enumerate(file_list):
        file_name = os.path.basename(file_path)
        
        # 分块阶段
        chunk_start = time.time()
        result = processor.process_file(file_path)
        chunk_end = time.time()
        chunk_time = chunk_end - chunk_start
        
        if "error" in result:
            print(f"  [{i+1}/{len(file_list)}] {file_name}: {result['error']}")
            continue
        
        chunks = result.get("chunks", [])
        if not chunks:
            print(f"  [{i+1}/{len(file_list)}] {file_name}: No content")
            continue
        
        # 向量化阶段
        vector_start = time.time()
        embeddings = embedder.encode(chunks)
        vector_end = time.time()
        vector_time = vector_end - vector_start
        
        # 添加到索引
        metas = []
        for j, chunk in enumerate(chunks):
            metadata = {
                "file_path": file_path,
                "file_name": file_name,
                "content": chunk,
                "category": extract_category(file_name),
                "chunk_index": j,
                "chunk_text": chunk[:100] if len(chunk) > 100 else chunk
            }
            metas.append(metadata)
        
        store.add(np.array(embeddings).astype('float32'), metas)
        
        all_metadata.extend(metas)
        total_chunk_time += chunk_time
        total_vector_time += vector_time
        total_chunks += len(chunks)
        
        per_file_stats.append({
            "file_name": file_name,
            "chunks": len(chunks),
            "chunk_time_ms": chunk_time * 1000,
            "vector_time_ms": vector_time * 1000
        })
        
        print(f"  [{i+1}/{len(file_list)}] {file_name}: {len(chunks)} chunks, "
              f"chunk {chunk_time*1000:.1f}ms, vector {vector_time*1000:.1f}ms")
    
    return {
        "metadata": len(all_metadata),
        "chunk_time": total_chunk_time,
        "vector_time": total_vector_time,
        "total_chunks": total_chunks,
        "per_file_stats": per_file_stats
    }


def extract_category(filename):
    """从文件名提取分类"""
    if '_' in filename:
        return filename.split('_')[0]
    if '-' in filename:
        return filename.split('-')[0]
    return os.path.splitext(filename)[0]


def evaluate_retrieval(store, embedder, query: str, expected_category: str, 
                       use_rewrite: bool = True) -> dict:
    """评估单次检索（以文件为单位去重计算）"""
    rewritten = None
    search_query = query
    if use_rewrite:
        use_deepseek = (LLM_TYPE == "deepseek")
        rewritten = rewrite_query_with_llm(query, use_deepseek=use_deepseek)
        search_query = rewritten
    
    # 向量化查询
    encode_start = time.time()
    query_vector = embedder.encode([search_query])[0]
    encode_time = time.time() - encode_start
    
    # 检索（获取更多结果以便去重）
    search_start = time.time()
    all_results = store.search(query_vector, k=20)  # 检索更多以便文件去重
    search_time = time.time() - search_start
    
    # 按文件去重（保持原有顺序）
    seen_files = set()
    unique_results = []
    for r in all_results:
        file_path = r.get('file_path', '')
        if file_path not in seen_files:
            seen_files.add(file_path)
            unique_results.append(r)
    
    # 取去重后的 top-3
    top_1_file = unique_results[:1]
    top_3_files = unique_results[:3]
    
    # P@1: top-1 文件是否匹配期望分类
    p_at_1 = 0.0
    for r in top_1_file:
        if r.get('category') == expected_category:
            p_at_1 = 1.0
            break
    
    # P@3: top-3 中有多少个不同文件匹配（去重后）
    hit_count = 0
    for r in top_3_files:
        if r.get('category') == expected_category:
            hit_count += 1
    p_at_3 = hit_count / 3.0
    
    return {
        "original_query": query,
        "rewritten_query": rewritten,
        "results": unique_results[:5],  # 返回去重后的前5个文件
        "all_results": unique_results,  # 保留完整去重结果用于MRR计算
        "hit": p_at_1 > 0 or p_at_3 > 0,
        "precision_at_1": p_at_1,
        "precision_at_3": p_at_3,
        "category_hits": {"top1": p_at_1 > 0, "top3": hit_count},
        "encode_time": encode_time,
        "search_time": search_time,
        "total_time": encode_time + search_time
    }


def print_result(result: dict, index: int = None):
    """打印单个检索结果（文件级别，去重）"""
    prefix = f"[{index}] " if index else ""
    
    print(f"\n{prefix}Query: {result['original_query']}")
    
    if result['rewritten_query']:
        print(f"      [Rewritten]: {result['rewritten_query']}")
    
    print(f"      Expected: {result.get('expected_category', 'N/A')}")
    
    # 使用 all_results（去重后的完整列表）显示前5个文件
    display_results = result.get('all_results', result['results'])[:5]
    for i, r in enumerate(display_results[:3]):  # 只显示前3
        category = r.get('category', 'unknown')
        filename = r.get('file_name', 'unknown')
        score = r.get('score', 0.0)
        match = "✓" if category == result.get('expected_category') else " "
        print(f"      {match} {i+1}. [{category}] {filename} (score: {score:.4f})")


def calculate_metrics(all_results: list) -> dict:
    """计算总体评估指标（以文件为单位）"""
    n = len(all_results)
    
    p_at_1 = [r['precision_at_1'] for r in all_results]
    p_at_3 = [r['precision_at_3'] for r in all_results]
    
    # MRR: 基于去重后的文件列表计算
    mrr = 0.0
    for r in all_results:
        expected = r.get('expected_category')
        for i, res in enumerate(r.get('all_results', r['results'])):
            if res.get('category') == expected:
                mrr += 1.0 / (i + 1)
                break
    
    # Hit Rate@3: top-3 中是否有任何匹配
    hit_at_3 = sum(1 for r in all_results if r['category_hits']['top3'] > 0)
    total_encode_time = sum(r['encode_time'] for r in all_results)
    total_search_time = sum(r['search_time'] for r in all_results)
    total_retrieval_time = total_encode_time + total_search_time
    
    return {
        "precision_at_1": round(float(np.mean(p_at_1)), 4),
        "precision_at_3": round(float(np.mean(p_at_3)), 4),
        "mrr": round(float(mrr / n if n > 0 else 0.0), 4),
        "hit_rate_at_3": round(float(hit_at_3 / n if n > 0 else 0.0), 4),
        "total": n,
        "hits": sum(1 for r in all_results if r['hit']),
        # 检索时间（总）
        "total_encode_time": round(float(total_encode_time), 4),
        "total_search_time": round(float(total_search_time), 4),
        "total_retrieval_time": round(float(total_retrieval_time), 4),
        # 检索时间（平均）
        "avg_encode_time": round(float(total_encode_time / n if n > 0 else 0), 4),
        "avg_search_time": round(float(total_search_time / n if n > 0 else 0), 4),
        "avg_retrieval_time": round(float(total_retrieval_time / n if n > 0 else 0), 4)
    }


def print_metrics(metrics: dict):
    """打印评估指标"""
    print("\n" + "=" * 60)
    print("EVALUATION METRICS")
    print("=" * 60)
    print(f"Total queries:       {metrics['total']}")
    print(f"Hits (top-3):        {metrics['hits']}/{metrics['total']}")
    print(f"Precision@1:        {metrics['precision_at_1']:.4f}")
    print(f"Precision@3:        {metrics['precision_at_3']:.4f}")
    print(f"MRR:                {metrics['mrr']:.4f}")
    print(f"Hit Rate@3:         {metrics['hit_rate_at_3']:.4f}")
    print("=" * 60)


def print_performance_stats(stats: dict, model_load_time: float, mem_stats: dict = None,
                             strategy_name: str = None, index_type: str = None, embedding_model: str = None):
    """打印性能统计
    
    Args:
        stats: 性能统计数据
        model_load_time: 模型加载时间
        mem_stats: 内存快照
        strategy_name: 分块策略名称
        index_type: 索引类型
        embedding_model: 嵌入模型名称
    """
    model_path = get_model_path(embedding_model) if embedding_model else ""
    model_size = get_model_folder_size(model_path) if model_path else 0
    actual_strategy = strategy_name if strategy_name else "Native"
    
    print("\n" + "=" * 60)
    print("PERFORMANCE STATISTICS")
    print("=" * 60)
    
    print(f"\n【Model Loading】")
    print(f"  Embedding Model: {embedding_model}")
    print(f"  Model Size: {format_size(model_size)}")
    print(f"  Load Time: {model_load_time:.2f}s")
    if mem_stats:
        print(f"  Memory After Load: {mem_stats['current_mb']} MB (peak: {mem_stats['peak_mb']} MB)")
    
    print(f"\n【Index Config】")
    print(f"  Index Type: {index_type}")
    print(f"  Chunking Strategy: {actual_strategy}")
    
    print(f"\n【Index Stats】")
    print(f"  Files Processed: {len(stats['per_file_stats'])}")
    print(f"  Total Chunks: {stats['total_chunks']}")
    print(f"  Index Vectors: {stats['metadata']}")
    print(f"  Index Size: {format_size(get_index_size())}")
    
    print(f"\n【Time Stats】")
    print(f"  Total Chunking Time: {stats['chunk_time']:.3f}s ({stats['chunk_time']*1000:.1f}ms)")
    print(f"  Total Vectorization Time: {stats['vector_time']:.3f}s ({stats['vector_time']*1000:.1f}ms)")
    
    if len(stats['per_file_stats']) > 0:
        print(f"\n【Average Times】")
        print(f"  Per File Chunking: {stats['chunk_time']/len(stats['per_file_stats'])*1000:.1f}ms")
        print(f"  Per File Vectorization: {stats['vector_time']/len(stats['per_file_stats'])*1000:.1f}ms")
    
    if stats['total_chunks'] > 0:
        print(f"  Per Chunk Vectorization: {stats['vector_time']/stats['total_chunks']*1000:.2f}ms")
    
    print("=" * 60)


def build_performance_data(stats: dict, model_load_time: float, mem_after_load: dict,
                             chunking_strategy: str, index_type: str, embedding_model: str) -> dict:
    """构建性能数据（用于导出）
    
    Args:
        stats: 性能统计数据
        model_load_time: 模型加载时间
        mem_after_load: 加载后的内存快照
        chunking_strategy: 分块策略名称
        index_type: 索引类型
        embedding_model: 嵌入模型名称
    """
    file_count = len(stats['per_file_stats'])
    model_path = get_model_path(embedding_model)
    model_size = get_model_folder_size(model_path)
    index_size = get_index_size()
    
    return {
        "meta": {
            "embedding_model": embedding_model,
            "model_path": model_path,
            "model_size": format_size(model_size),
            "model_load_time": round(model_load_time, 2),
            "index_type": index_type,
            "chunking_strategy": chunking_strategy,
            "index_size": format_size(index_size)
        },
        "memory": {
            "after_load_mb": round(mem_after_load['current_mb'], 2),
            "peak_mb": round(mem_after_load['peak_mb'], 2)
        },
        "stats": {
            "file_count": file_count,
            "total_chunks": stats['total_chunks'],
            "vector_count": stats['metadata'],
            "chunk_time": round(stats['chunk_time'], 4),
            "vector_time": round(stats['vector_time'], 4),
            "avg_chunk_per_file": round(stats['chunk_time'] / file_count * 1000, 2) if file_count > 0 else 0,
            "avg_vector_per_file": round(stats['vector_time'] / file_count * 1000, 2) if file_count > 0 else 0,
            "avg_vector_per_chunk": round(stats['vector_time'] / stats['total_chunks'] * 1000, 2) if stats['total_chunks'] > 0 else 0
        }
    }


# ============================================================
# 单次评估流程
# ============================================================

def run_single_evaluation(strategy, strategy_name, index_type, embedding_model):
    """运行单次评估
    
    Args:
        strategy: 分块策略对象，None 表示使用原生默认策略
        strategy_name: 策略名称
        index_type: 索引类型
        embedding_model: 嵌入模型名称
    """
    print("\n" + "=" * 60)
    print(f"Evaluating: {strategy_name} | Index: {index_type} | Model: {embedding_model}")
    print("=" * 60)
    
    # 加载测试用例
    with open(TEST_CASES_FILE, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)[CURRENT_TEST_TYPE]
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
    embedder, store, model_load_time, model_path = setup_index(index_type, embedding_model)
    mem_after_load = snapshot_memory()
    
    # 打印模型信息
    model_size = get_model_folder_size(model_path)
    print(f"   Model size: {format_size(model_size)}")
    print(f"   Memory after load: {mem_after_load['current_mb']} MB (peak: {mem_after_load['peak_mb']} MB)")
    
    # 创建文件处理器
    processor = FileProcessor()
    if strategy:
        processor.chunking_strategy = strategy
    
    # Step 3: 索引测试文件
    print("\n[Step 3] Indexing test files...")
    files = get_files_from_config(test_path, CURRENT_TEST_TYPE)
    print(f"[Step 3] Found {len(files)} files\n")
    
    index_start = time.time()
    index_stats = index_files_with_timing(store, files, embedder, processor)
    index_time = time.time() - index_start
    
    # 保存索引
    save_start = time.time()
    store.save()
    save_time = time.time() - save_start
    
    print(f"\n[Step 3] Indexed {index_stats['metadata']} chunks in {index_time:.2f}s")
    print(f"[Step 3] Save time: {save_time:.2f}s")
    
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
        print(f"      [Time: encode {result['encode_time']*1000:.1f}ms, search {result['search_time']*1000:.1f}ms]")
    
    # Step 5: 计算并打印指标
    metrics = calculate_metrics(all_results)
    print_metrics(metrics)
    
    # Step 6: 打印性能统计
    performance = build_performance_data(index_stats, model_load_time, mem_after_load, strategy_name, index_type, embedding_model)
    print_performance_stats(index_stats, model_load_time, mem_after_load, strategy_name, index_type, embedding_model)
    
    # Step 7: 导出结果
    reporter = EvalReporter()
    json_path, seq = reporter.export(
        test_type=CURRENT_TEST_TYPE,
        embedding_model=embedding_model,
        index_type=index_type,
        chunking_name=strategy_name,
        metrics=metrics,
        performance=performance
    )
    
    txt_path = reporter.export_text(
        test_type=CURRENT_TEST_TYPE,
        embedding_model=embedding_model,
        index_type=index_type,
        chunking_name=strategy_name,
        metrics=metrics,
        performance=performance,
        seq=seq
    )
    
    print(f"\n[Export] Results saved to:")
    print(f"  JSON: {json_path}")
    print(f"  TXT:  {txt_path}")
    
    return metrics, index_stats


# ============================================================
# 主流程
# ============================================================

def main():
    # 启动内存追踪
    tracemalloc.start()
    
    print("=" * 60)
    print("AIFileSearcher Retrieval Evaluation")
    print("=" * 60)
    
    # 获取遍历列表（None 转为空列表）
    embedding_models = ALL_EMBEDDING_MODELS if ALL_EMBEDDING_MODELS else []
    chunking_strategies = ALL_CHUNKING_STRATEGIES if ALL_CHUNKING_STRATEGIES else []
    index_types = ALL_INDEX_TYPES if ALL_INDEX_TYPES else []
    
    # 如果全部为空，报错退出
    if not embedding_models and not chunking_strategies and not index_types:
        print("[Error] No configurations to iterate!")
        print("  - Set ALL_EMBEDDING_MODELS to iterate embedding models")
        print("  - Set ALL_CHUNKING_STRATEGIES to iterate chunking strategies")
        print("  - Set ALL_INDEX_TYPES to iterate index types")
        return
    
    # 补充默认值：确保每个维度至少有一项
    if not embedding_models:
        embedding_models = ["bge-base-zh-v1.5"]
    if not chunking_strategies:
        chunking_strategies = [None]  # None = 使用原生默认策略
    if not index_types:
        index_types = ["IndexFlatL2"]
    
    # 计算总测试次数
    total_tests = len(embedding_models) * len(chunking_strategies) * len(index_types)
    
    print(f"\n【Configuration】")
    print(f"  Embedding Models: {embedding_models}")
    print(f"  Index Types: {index_types}")
    print(f"  Chunking Strategies: {[get_strategy_name(s) for s in chunking_strategies]}")
    print(f"  Total Tests: {total_tests}")
    print(f"  LLM Rewrite: {'Enabled' if ENABLE_QUERY_REWRITE else 'Disabled'}")
    print(f"  LLM Type: {LLM_TYPE}")
    print(f"  Test Type: {CURRENT_TEST_TYPE}")
    
    # 三层嵌套遍历
    results_summary = []
    test_count = 0
    
    for embedding_model in embedding_models:
        for strategy in chunking_strategies:
            strategy_name = get_strategy_name(strategy)
            for index_type in index_types:
                test_count += 1
                print(f"\n[Test {test_count}/{total_tests}]")
                
                metrics, stats = run_single_evaluation(
                    strategy=strategy,
                    strategy_name=strategy_name,
                    index_type=index_type,
                    embedding_model=embedding_model
                )
                
                results_summary.append({
                    "embedding_model": embedding_model,
                    "strategy": strategy_name,
                    "index_type": index_type,
                    "metrics": metrics,
                    "chunks": stats['total_chunks']
                })
    
    # 打印汇总
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"{'Model':<25} {'Strategy':<25} {'Index':<15} {'P@1':>6} {'P@3':>6} {'MRR':>6}")
    print("-" * 90)
    for r in results_summary:
        m = r['metrics']
        print(f"{r['embedding_model']:<25} {r['strategy']:<25} {r['index_type']:<15} "
              f"{m['precision_at_1']:>6.4f} {m['precision_at_3']:>6.4f} {m['mrr']:>6.4f}")
    print("=" * 90)
    
    print("\n[Done] All evaluations complete!")


if __name__ == "__main__":
    main()
