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
    CURRENT_TEST_TYPE, EMBEDDING_MODEL, EMBEDDING_MODEL_PATH, INDEX_TYPE, 
    CHUNKING_STRATEGY, ENABLE_QUERY_REWRITE, LLM_TYPE, PROJECT_ROOT,
    get_chunking_name
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


def get_memory_usage_mb() -> float:
    """获取当前进程内存占用（MB）"""
    current, _ = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)


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


def setup_index():
    """初始化索引"""
    clear_index_files()
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("Loading embedding model...")
    print("=" * 60)
    
    model_load_start = time.time()
    embedder = EmbeddingModel(model_name=EMBEDDING_MODEL)
    model_load_time = time.time() - model_load_start
    
    dimension = embedder.model.get_sentence_embedding_dimension()
    
    print(f"\n✅ Embedding model loaded")
    print(f"   Model: {EMBEDDING_MODEL}")
    print(f"   Dimension: {dimension}")
    print(f"   Load time: {model_load_time:.2f}s")
    
    print(f"\n📊 Creating index: {INDEX_TYPE}")
    store = VectorStore(
        dimension=dimension,
        index_path=get_data_path("faiss_index.bin"),
        metadata_path=get_data_path("metadata.json"),
        index_type=INDEX_TYPE
    )
    
    print(f"   Index type: {type(store.index).__name__}")
    
    return embedder, store, model_load_time


def get_files_from_config(test_path: str, test_type: str) -> list:
    """从配置路径获取测试文件"""
    ext = f".{test_type}"
    files = []
    for filename in os.listdir(test_path):
        if filename.endswith(ext):
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
    """评估单次检索"""
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
    
    # 检索
    search_start = time.time()
    results = store.search(query_vector, k=5)
    search_time = time.time() - search_start
    
    top_1 = results[:1]
    top_3 = results[:3]
    
    p_at_1 = 0.0
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
        "category_hits": {"top1": p_at_1 > 0, "top3": hit_count},
        "encode_time": encode_time,
        "search_time": search_time,
        "total_time": encode_time + search_time
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
    
    mrr = 0.0
    for r in all_results:
        for i, res in enumerate(r['results']):
            if res.get('category') == r.get('expected_category'):
                mrr += 1.0 / (i + 1)
                break
    
    hit_at_3 = sum(1 for r in all_results if r['category_hits']['top3'] > 0)
    total_encode_time = sum(r['encode_time'] for r in all_results)
    total_search_time = sum(r['search_time'] for r in all_results)
    
    return {
        "precision_at_1": float(np.mean(p_at_1)),
        "precision_at_3": float(np.mean(p_at_3)),
        "mrr": float(mrr / n if n > 0 else 0.0),
        "hit_rate_at_3": float(hit_at_3 / n if n > 0 else 0.0),
        "total": n,
        "hits": sum(1 for r in all_results if r['hit']),
        "avg_encode_time": float(total_encode_time / n if n > 0 else 0),
        "avg_search_time": float(total_search_time / n if n > 0 else 0),
        "avg_total_time": float((total_encode_time + total_search_time) / n if n > 0 else 0)
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


def print_performance_stats(stats: dict, model_load_time: float, mem_stats: dict = None):
    """打印性能统计"""
    model_size = get_model_folder_size(EMBEDDING_MODEL_PATH)
    
    print("\n" + "=" * 60)
    print("PERFORMANCE STATISTICS")
    print("=" * 60)
    
    print(f"\n【Model Loading】")
    print(f"  Embedding Model: {EMBEDDING_MODEL}")
    print(f"  Model Size: {format_size(model_size)}")
    print(f"  Load Time: {model_load_time:.2f}s")
    if mem_stats:
        print(f"  Memory After Load: {mem_stats['current_mb']} MB (peak: {mem_stats['peak_mb']} MB)")
    
    print(f"\n【Index Config】")
    print(f"  Index Type: {INDEX_TYPE}")
    print(f"  Chunking Strategy: {get_chunking_name()}")
    
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


def build_performance_data(stats: dict, model_load_time: float, mem_after_load: dict) -> dict:
    """构建性能数据（用于导出）"""
    file_count = len(stats['per_file_stats'])
    model_size = get_model_folder_size(EMBEDDING_MODEL_PATH)
    
    return {
        "meta": {
            "embedding_model": EMBEDDING_MODEL,
            "model_path": EMBEDDING_MODEL_PATH,
            "model_size": format_size(model_size),
            "model_load_time": model_load_time,
            "index_type": INDEX_TYPE,
            "chunking_strategy": get_chunking_name(),
            "index_size": format_size(get_index_size())
        },
        "memory": {
            "after_load_mb": mem_after_load['current_mb'],
            "peak_mb": mem_after_load['peak_mb']
        },
        "stats": {
            "file_count": file_count,
            "total_chunks": stats['total_chunks'],
            "vector_count": stats['metadata'],
            "chunk_time": stats['chunk_time'],
            "vector_time": stats['vector_time'],
            "avg_chunk_per_file": stats['chunk_time'] / file_count * 1000 if file_count > 0 else 0,
            "avg_vector_per_file": stats['vector_time'] / file_count * 1000 if file_count > 0 else 0,
            "avg_vector_per_chunk": stats['vector_time'] / stats['total_chunks'] * 1000 if stats['total_chunks'] > 0 else 0
        }
    }


# ============================================================
# 主流程
# ============================================================

def main():
    # 启动内存追踪
    tracemalloc.start()
    
    print("=" * 60)
    print("AIFileSearcher Retrieval Evaluation")
    print("=" * 60)
    
    print(f"\n【Configuration】")
    print(f"  Embedding Model: {EMBEDDING_MODEL}")
    print(f"  Index Type: {INDEX_TYPE}")
    print(f"  Chunking Strategy: {get_chunking_name()}")
    print(f"  LLM Rewrite: {'Enabled' if ENABLE_QUERY_REWRITE else 'Disabled'}")
    print(f"  LLM Type: {LLM_TYPE}")
    print(f"  Test Type: {CURRENT_TEST_TYPE}")
    
    # 加载测试用例
    with open(TEST_CASES_FILE, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)[CURRENT_TEST_TYPE]
    test_queries = test_cases["queries"]
    test_path = test_cases["path"]
    
    print(f"\n[Config] Test path: {test_path}")
    print(f"[Config] Queries: {len(test_queries)}")
    
    # Step 1: 清空索引
    print("\n[Step 1] Clearing index...")
    deleted = clear_index_files()
    print(f"[Step 1] Deleted files: {deleted}")
    
    # Step 2: 初始化索引
    print("\n[Step 2] Initializing index...")
    embedder, store, model_load_time = setup_index()
    mem_after_load = snapshot_memory()
    
    # 打印模型信息
    model_size = get_model_folder_size(EMBEDDING_MODEL_PATH)
    print(f"   Model size: {format_size(model_size)}")
    print(f"   Memory after load: {mem_after_load['current_mb']} MB (peak: {mem_after_load['peak_mb']} MB)")
    
    # 创建文件处理器
    processor = FileProcessor()
    if CHUNKING_STRATEGY:
        processor.chunking_strategy = CHUNKING_STRATEGY
    
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
    performance = build_performance_data(index_stats, model_load_time, mem_after_load)
    print_performance_stats(index_stats, model_load_time, mem_after_load)
    
    # Step 7: 导出结果
    reporter = EvalReporter()
    json_path, seq = reporter.export(
        test_type=CURRENT_TEST_TYPE,
        embedding_model=EMBEDDING_MODEL,
        index_type=INDEX_TYPE,
        chunking_name=get_chunking_name(),
        metrics=metrics,
        performance=performance
    )
    
    txt_path = reporter.export_text(
        test_type=CURRENT_TEST_TYPE,
        embedding_model=EMBEDDING_MODEL,
        index_type=INDEX_TYPE,
        chunking_name=get_chunking_name(),
        metrics=metrics,
        performance=performance,
        seq=seq
    )
    
    print(f"\n[Export] Results saved to:")
    print(f"  JSON: {json_path}")
    print(f"  TXT:  {txt_path}")
    
    print("\n[Done] Evaluation complete!")


if __name__ == "__main__":
    main()
