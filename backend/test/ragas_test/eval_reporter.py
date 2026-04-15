"""评估结果导出模块"""

import os
import json
from datetime import datetime


class EvalReporter:
    """评估结果导出器"""

    def __init__(self, result_dir: str = None):
        if result_dir is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            result_dir = os.path.join(backend_dir, "test", "ragas_test", "result")
        
        self.result_dir = result_dir
        os.makedirs(result_dir, exist_ok=True)

    def _get_next_seq(self, base_name: str) -> str:
        """获取下一个序号"""
        existing = []
        for f in os.listdir(self.result_dir):
            if f.startswith(base_name) and f.endswith(".json"):
                try:
                    seq = int(f.split("-")[-1].replace(".json", ""))
                    existing.append(seq)
                except ValueError:
                    continue
        
        next_seq = 1
        if existing:
            next_seq = max(existing) + 1
        
        return f"{base_name}-{next_seq}.json"

    def export(self, 
               test_type: str,
               embedding_model: str,
               index_type: str,
               chunking_name: str,
               metrics: dict,
               performance: dict,
               config: dict = None) -> str:
        """
        导出评估结果到 JSON 文件
        
        Returns:
            str: 导出文件的完整路径
        """
        base_name = f"{test_type}-{embedding_model}-{index_type}-{chunking_name}"
        filename = self._get_next_seq(base_name)
        filepath = os.path.join(self.result_dir, filename)

        result = {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "test_type": test_type,
                "embedding_model": embedding_model,
                "index_type": index_type,
                "chunking_strategy": chunking_name,
            },
            "config": config or {},
            "metrics": metrics,
            "performance": performance
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return filepath

    def export_text(self,
                    test_type: str,
                    embedding_model: str,
                    index_type: str,
                    chunking_name: str,
                    metrics: dict,
                    performance: dict,
                    query_results: list = None) -> str:
        """
        导出评估结果到文本文件
        
        Returns:
            str: 导出文件的完整路径
        """
        base_name = f"{test_type}-{embedding_model}-{index_type}-{chunking_name}"
        filename = self._get_next_seq(base_name).replace(".json", ".txt")
        filepath = os.path.join(self.result_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("EVALUATION METRICS\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total queries:       {metrics.get('total', 0)}\n")
            f.write(f"Hits (top-3):        {metrics.get('hits', 0)}/{metrics.get('total', 0)}\n")
            f.write(f"Precision@1:        {metrics.get('precision_at_1', 0):.4f}\n")
            f.write(f"Precision@3:        {metrics.get('precision_at_3', 0):.4f}\n")
            f.write(f"MRR:                {metrics.get('mrr', 0):.4f}\n")
            f.write(f"Hit Rate@3:         {metrics.get('hit_rate_at_3', 0):.4f}\n")
            f.write("\n")
            f.write("=" * 60 + "\n")
            f.write("PERFORMANCE STATISTICS\n")
            f.write("=" * 60 + "\n")
            
            perf_meta = performance.get('meta', {})
            f.write(f"\n【Model Loading】\n")
            f.write(f"  Embedding Model: {perf_meta.get('embedding_model', 'N/A')}\n")
            f.write(f"  Model Size: {perf_meta.get('model_size', 'N/A')}\n")
            f.write(f"  Load Time: {perf_meta.get('model_load_time', 0):.2f}s\n")
            
            memory = performance.get('memory', {})
            if memory:
                f.write(f"  Memory After Load: {memory.get('after_load_mb', 'N/A')} MB\n")
                f.write(f"  Peak Memory: {memory.get('peak_mb', 'N/A')} MB\n")
            
            f.write(f"\n【Index Config】\n")
            f.write(f"  Index Type: {perf_meta.get('index_type', 'N/A')}\n")
            f.write(f"  Chunking Strategy: {perf_meta.get('chunking_strategy', 'N/A')}\n")
            
            perf_stats = performance.get('stats', {})
            f.write(f"\n【Index Stats】\n")
            f.write(f"  Files Processed: {perf_stats.get('file_count', 0)}\n")
            f.write(f"  Total Chunks: {perf_stats.get('total_chunks', 0)}\n")
            f.write(f"  Index Vectors: {perf_stats.get('vector_count', 0)}\n")
            f.write(f"  Index Size: {perf_stats.get('index_size', 'N/A')}\n")
            
            f.write(f"\n【Time Stats】\n")
            f.write(f"  Total Chunking Time: {perf_stats.get('chunk_time', 0):.3f}s\n")
            f.write(f"  Total Vectorization Time: {perf_stats.get('vector_time', 0):.3f}s\n")
            
            if perf_stats.get('file_count', 0) > 0:
                f.write(f"\n【Average Times】\n")
                f.write(f"  Per File Chunking: {perf_stats.get('avg_chunk_per_file', 0):.1f}ms\n")
                f.write(f"  Per File Vectorization: {perf_stats.get('avg_vector_per_file', 0):.1f}ms\n")
            
            if perf_stats.get('total_chunks', 0) > 0:
                f.write(f"  Per Chunk Vectorization: {perf_stats.get('avg_vector_per_chunk', 0):.2f}ms\n")

        return filepath
